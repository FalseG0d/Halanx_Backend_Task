import json
import logging
import random
from datetime import datetime, timedelta

import pytz
import requests
import sendgrid
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from celery import shared_task
from decouple import config
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.db.models import Q, Sum, Case, When, IntegerField, F, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sendgrid.helpers.mail import Email, Content, Mail

from BatchBase.models import Batch
from Carts.models import ProductItem
from Homes.Tenants.utils import avail_tenant_refer_and_earn
from News.tasks import add_articles_to_feed
from Notifications.models import Notification
from Notifications.utils import ORDER_DELIVERED_NC, NotificationCategories, ANNOUNCEMENT_NC, FOLLOW_USER_NC
from Products.models import Product
from Promotions.models import Campaign
from ShopperBase.models import Shopper
from Transaction.utils import verify_transaction
from UserBase.fb_template_creator import draw_template
from UserBase.models import Customer, OTP, SpamReport, UserInterest, Education, Work, Contact, Picture, EmailOTP
from UserBase.serializers import (PublicUserSerializer, UserProfileSerializer, UserFollowerListSerializer,
                                  ProductSerializer, UserSerializer, PictureSerializer,
                                  UserInterestSerializer, EducationSerializer, WorkSerializer, ContactSerializer)
from UserBase.tasks import track_customer_visit, send_email_otp
from UserBase.utils import CUSTOMER_UPDATABLE_FIELDS, TENANT_REFERRAL, \
    get_referral_code_type, avail_customer_refer_and_earn, GenderChoices
from utility.campaign_utils import parse_campaign_code
from utility.geo_utils import find_distance
from utility.logging_utils import sentry_debug_logger
from utility.pagination_utils import StandardPagination
from utility.render_response_utils import STATUS, SUCCESS, ERROR
from utility.serializers import PlaceTileSerializer, CustomerSerializer, HalanxCustomerSerializer
from utility.sms_utils import send_sms
from utility.time_utils import is_valid_datetime

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
def verify_email(request):
    """
    get:
    verify the email passed as parameter
    ToDo: hashing of the email verification link
    """
    email = request.GET.get("email")
    customer = Customer.objects.filter(user__email=email).first()
    if customer:
        customer.is_email_verified = True
        customer.save()
        return redirect("https://halanx.com/email-verification-success.html")
    else:
        return redirect("https://halanx.com/email-verification-failure.html")


@api_view(['POST'])
def register(request):
    """
    post:
    Register a new user as customer
    required fields: email, username, password, first_name, last_name, phone_no, otp
    optional fields: gender, dob
    """
    # check if all required fields provided
    required = ['username', 'password', 'first_name', 'last_name', 'phone_no', 'otp']
    if not all([request.data.get(field) for field in required]):
        return Response({"error": "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)

    # validate otp
    otp = get_object_or_404(OTP, phone_no=request.data.get('phone_no'))
    if request.data.get('otp') != otp.password:
        return Response({"error": "Wrong OTP!"}, status=status.HTTP_400_BAD_REQUEST)

    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone_no = request.data.get('phone_no')
    gender = request.data.get('gender')
    dob = request.data.get('dob')

    # check if customer has unique phone number
    if Customer.objects.filter(is_registered=True, phone_no=phone_no).exists():
        print(4)
        return Response({"error": "Customer with this Phone Number already exists!"}, status=status.HTTP_409_CONFLICT)

    # customer exists but not registered
    existing_unregistered_customer = Customer.objects.filter(phone_no=phone_no, is_registered=False).first()
    if existing_unregistered_customer:
        customer = existing_unregistered_customer
        customer.is_registered = True
        customer.save()
        User.objects.filter(id=customer.user.id).update(email=email, password=password, first_name=first_name,
                                                        last_name=last_name)
        user = customer.user
    else:
        try:
            user = User.objects.create_user(username=username, password=password, email=email,
                                            first_name=first_name, last_name=last_name)
        except IntegrityError:
            user = User.objects.get(username=username)
        if user.pk is None:
            return Response({"error": "New user could not be created."}, status=status.HTTP_400_BAD_REQUEST)

        customer = Customer.objects.create(user=user, phone_no=phone_no)

        # add referral if ref_id='some_ref_id' like nimJcy
        try:
            if 'ref_id' in request.query_params:
                from Homes.Tenants.models import TenantRequirement
                from Homes.Tenants.models import Tenant
                tenant, created = Tenant.objects.get_or_create(customer=customer)
                tenant_requirement, created = TenantRequirement.objects.get_or_create(
                    phone_no=phone_no, tenant=tenant, affiliate_code=request.query_params['ref_id'])
                if created:
                    print("tenant requirement created with id", tenant_requirement.id)
        except Exception as E:
            sentry_debug_logger.error("error in adding referral" + str(E), exc_info=True)

    # set gender
    if gender in list(zip(*GenderChoices))[0]:
        customer.gender = gender

    # set dob
    if dob and is_valid_datetime(dob, "%d-%m-%Y"):
        customer.dob = datetime.strptime(dob, "%d-%m-%Y")

    customer.save()

    token, created = Token.objects.get_or_create(user=user)
    return Response({"key": token.key}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def register_social(request):
    """
    post:
    Register new user by social account
    required fields: phone_no, otp
    optional fields: email, first_name, last_name, gender, dob
    """
    # check if all required fields provided
    required = ['phone_no', 'otp']
    if not all([request.data.get(field) for field in required]):
        return Response({"error": "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)

    # otp validation
    otp = get_object_or_404(OTP, phone_no=request.data.get('phone_no'))
    if request.data.get('otp') != otp.password:
        return Response({"error": "Wrong OTP!"}, status=status.HTTP_400_BAD_REQUEST)

    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone_no = request.data.get('phone_no')
    gender = request.data.get('gender')
    dob = request.data.get('dob')
    username = 'c' + phone_no

    # check if customer already exists
    if Customer.objects.filter(is_registered=True, phone_no=phone_no).exists() or \
            Customer.objects.filter(user=request.user).exists() or \
            User.objects.filter(username=username).exists():
        return Response({"error": "Customer already exists"}, status=status.HTTP_409_CONFLICT)

    # update user details
    user = request.user
    user.username = username
    if email:
        user.email = email
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.save()

    # customer exists with same phone number but not registered
    existing_customer = Customer.objects.filter(phone_no=request.data.get('phone_no'), is_registered=False).first()
    if existing_customer:
        existing_customer.user = user
        existing_customer.save()
        customer = existing_customer
    else:
        # create customer
        customer = Customer(user=user, phone_no=request.data.get('phone_no'))

    # set gender
    if gender in list(zip(*GenderChoices))[0]:
        customer.gender = gender

    # set dob
    if dob and is_valid_datetime(dob, "%d-%m-%Y"):
        customer.dob = datetime.strptime(dob, "%d-%m-%Y")

    customer.save()

    logger.debug("Customer created through FB!")
    return Response({"status": "success"}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def generate_otp(request, phone_no):
    """
    post:
    Generate OTP for requested mobile number
    """
    rand = random.randrange(1, 8999) + 1000
    message = "Hi {}! {} is your One Time Password(OTP) for Halanx App.".format(
        request.data.get('first_name', ''), rand)
    otp, created = OTP.objects.get_or_create(phone_no=phone_no)
    otp.password = rand
    otp.save()

    send_sms.delay(phone_no, message)
    return Response({"result": "success"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def generate_email_otp(request):
    email = request.data['email']
    email_otp = EmailOTP.objects.filter(email=email).first()
    if email_otp:
        email_otp.password = random.randint(1000, 9999)
        email_otp.save()
    else:
        email_otp = EmailOTP.objects.create(email=email, password=random.randint(1000, 9999))

    send_email_otp.delay(email_otp.email, email_otp.password)

    return Response({STATUS: SUCCESS, 'message': 'OTP sent succesfully on your Email. Enter the OTP to verify your '
                                                 'email'})


@api_view(['POST'])
def login_with_otp(request):
    """
    post:
    Generate token for user
    """
    phone_no = request.data.get('username')[1:]
    customer = get_object_or_404(Customer, phone_no=phone_no)
    user = customer.user
    otp = get_object_or_404(OTP, phone_no=phone_no, password=request.data.get('password'))
    if otp.timestamp >= timezone.now() - timedelta(minutes=10):
        token, created = Token.objects.get_or_create(user=user)
        return Response({"key": token.key}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_exists(request, phone_no):
    """
    get:
    check if user exists or not
    """
    if Customer.objects.filter(is_registered=True, phone_no=phone_no).exists():
        return Response({"exists": "True"}, status=status.HTTP_200_OK)
    else:
        return Response({"exists": "False"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def user_logout(request):
    """
    post:
    logout the user by deleting current auth token
    """
    request.user.auth_token.delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_detail(request):
    """
    get:
    Get details of user who made request
    patch:
    Update the details of user who made request
    """
    customer = get_object_or_404(Customer.objects.select_related('user').
                                 prefetch_related('favorite_items', 'user_interests',
                                                  'favorite_places', 'follows'), user=request.user)

    if request.method == 'GET':
        serializer = UserSerializer(customer)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        data = {}
        for field in CUSTOMER_UPDATABLE_FIELDS:
            if request.data.get(field) is not None:
                data[field] = request.data[field]

        if data.get('campaign'):
            campaign_code = parse_campaign_code(data['campaign'])
            campaign = Campaign.objects.filter(code=campaign_code).first()
            if campaign:
                customer.campaign = campaign
                customer.save()
            data.pop('campaign')

        serializer = UserSerializer(customer, data=data, partial=True)
        if serializer.is_valid():
            if data.get('dob'):
                data['dob'] = datetime.strptime(data['dob'], "%d-%m-%Y").strftime('%Y-%m-%d')
            if data.get('email'):
                customer.user.email = data['email']
                customer.user.save()
            if data.get('first_name'):
                customer.user.first_name = data['first_name']
                customer.user.save()
            if data.get('last_name'):
                customer.user.last_name = data['last_name']
                customer.user.save()
            if customer.clatitude is None or customer.clongitude is None:
                data['clatitude'] = customer.dlatitude
                data['clongitude'] = customer.dlongitude
            updated_customer = serializer.update(customer, data)
            return Response(UserSerializer(updated_customer).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_location(request):
    """
    patch:
    Update user current location and track customer visit.
    """
    customer = get_object_or_404(Customer, user=request.user)

    clatitude = request.data.get('clatitude')
    clongitude = request.data.get('clongitude')
    dlatitude = request.data.get('dlatitude')
    dlongitude = request.data.get('dlongitude')

    if clatitude and clongitude:
        customer.clatitude, customer.clongitude = float(clatitude), float(clongitude)

    if dlatitude and dlongitude:
        customer.dlatitude, customer.dlongitude = float(dlatitude), float(dlongitude)
    customer.save()
    track_customer_visit.delay(customer.id)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_refer_and_earn(request):
    """
    avail refer and earn
    """
    if request.data.get("referral_code"):
        referral_code = request.data['referral_code']
        customer = get_object_or_404(Customer, user=request.user)

        if get_referral_code_type(referral_code) == TENANT_REFERRAL:
            if avail_tenant_refer_and_earn(customer, referral_code):
                return Response({"detail": "Successfully availed cashback from tenant refer & earn!"})
        else:
            if avail_customer_refer_and_earn(customer, referral_code):
                return Response({"detail": "Successfully availed cashback from customer refer & earn!"})
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_id(request, pk):
    """
    get:
    Get user details by id
    """
    try:
        customer = Customer.objects.select_related('user').prefetch_related('favorite_items',
                                                                            'user_interests', 'favorite_places',
                                                                            'follows', 'followed_by').get(pk=pk)
    except Customer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = PublicUserSerializer(customer, context={'request': request})
    serializer_data = serializer.data
    return Response(serializer_data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_album(request, pk):
    """
    get:
    get user pictures
    """
    customer = get_object_or_404(Customer, pk=pk)
    pictures = customer.pictures.filter(is_deleted=False)
    serializer = PictureSerializer(pictures, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_picture_list(request):
    """
    get:
    get all pictures of customer who made request
    post:
    create a new picture
    """
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == 'GET':
        if request.query_params.get('is_profile_pic', None):
            pictures = customer.pictures.filter(is_deleted=False, is_profile_pic=True)
        else:
            pictures = customer.pictures.filter(is_deleted=False)

        serializer = PictureSerializer(pictures, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        data['customer'] = customer.id
        serializer = PictureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_picture(request, pk):
    """
    get:
    get user picture by id
    patch:
    update picture by id
    delete:
    delete picture by id
    """
    picture = get_object_or_404(Picture, pk=pk, is_deleted=False)

    if request.method == 'GET':
        serializer = PictureSerializer(picture)
        return Response(serializer.data)

    elif request.method == 'PATCH' and picture.customer.user == request.user:
        serializer = PictureSerializer(picture, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.update(picture, request.data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE' and picture.customer.user == request.user:
        picture.is_deleted = True
        picture.save()
        return Response({"status": "Successfully deleted!"}, status=status.HTTP_204_NO_CONTENT)
    else:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def my_followers_list(request):
    """
    get:
    Get list of followers of user
    """
    customer = get_object_or_404(Customer.objects.prefetch_related('follows'), user=request.user)
    followers = customer.followed_by.all()
    serializer = UserFollowerListSerializer(followers, many=True, context={'me': customer})
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def my_following_list(request):
    """
    get:
    Get list of user followed by user
    """
    customer = get_object_or_404(Customer.objects.prefetch_related('follows'), user=request.user)
    following = customer.follows.all()
    serializer = UserFollowerListSerializer(following, many=True, context={'me': customer})
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_followers_list(request, pk):
    """
    get:
    Get list of followers of user by pk
    """
    me = get_object_or_404(Customer, user=request.user)
    customer = get_object_or_404(Customer.objects.prefetch_related('followed_by'), pk=pk)
    followers = customer.followed_by.all()
    serializer = UserFollowerListSerializer(followers, many=True, context={'me': me})
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_following_list(request, pk):
    """
    get:
    Get list of user followed by user by pk
    """
    me = get_object_or_404(Customer, user=request.user)
    customer = get_object_or_404(Customer.objects.prefetch_related('follows'), pk=pk)
    following = customer.follows.all()
    serializer = UserFollowerListSerializer(following, many=True, context={'me': me})
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_favorite_items_list(request):
    """
    get:
    Get favorite items of user
    """
    try:
        customer = Customer.objects.prefetch_related('favorite_items').get(user=request.user)
    except Customer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = ProductSerializer(customer.favorite_items.all(), many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_favorite_places_list(request):
    """
    get:
    Get favorite items of user
    """
    customer = get_object_or_404(Customer.objects.prefetch_related('favorite_places'), user=request.user)
    serializer = PlaceTileSerializer(customer.favorite_places.all(), many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_follow_toggle(request, pk):
    """
    patch:
    follow user toggle
    """
    customer = get_object_or_404(Customer.objects.prefetch_related('follows'), user=request.user)
    to_follow = get_object_or_404(Customer.objects.only('id'), pk=pk)

    if to_follow not in customer.follows.all():
        customer.follows.add(to_follow)
        # It is the payload that will be used for filtering further
        following_user_data = CustomerSerializer(customer).data
        notification_payload = {'sender': [following_user_data, ]}
        # example usage notification_payload = {'user': user data json}

        Notification(target=to_follow, category=FOLLOW_USER_NC, payload=notification_payload).save(
            data={'sender_name': customer.name, 'user': customer.id}, payload=notification_payload)

        return Response({"result": "followed"}, status=status.HTTP_200_OK)
    else:
        customer.follows.remove(to_follow)
        # Todo Delete the notification
        return Response({"result": "unfollowed"}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_favorite_items_toggle(request, pk):
    """
    patch:
    toggle item in favorite list
    """
    customer = get_object_or_404(Customer.objects.prefetch_related('favorite_items'), user=request.user)
    product = get_object_or_404(Product, pk=pk)

    if product not in customer.favorite_items.all():
        customer.favorite_items.add(product)
        return Response({"result": "favorited"}, status=status.HTTP_200_OK)
    else:
        customer.favorite_items.remove(product)
        return Response({"result": "unfavorited"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_rate_shopper(request):
    """
    post:
    Rate shopper on successful delivery of batch
    ToDo: prevent multiple rating
    """
    customer = get_object_or_404(Customer, user=request.user)
    batch = get_object_or_404(Batch, id=request.data.get('batch_id'))
    shopper = get_object_or_404(Shopper, id=request.data.get('shopper_id'))
    shopper.avg_rating = (shopper.avg_rating * shopper.n + request.data.get('rating')) / (shopper.n + 1)
    shopper.n += 1
    shopper.save()

    order = ProductItem.objects.filter(batch=batch, cart__customer=customer).first().order
    order.save()
    if order.is_delivered:
        _ = Notification(target=customer, category=ORDER_DELIVERED_NC).save(data={"order": order.id})
    return Response({"result": "Shopper successfully rated"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_add_balance(request):
    """
	post: 
	Add wallet balance to user account
	"""
    customer = get_object_or_404(Customer, user=request.user)
    data = request.data
    if data.get('transaction_id') and data.get('value') and data.get('gateway'):
        transaction_status = verify_transaction(data['transaction_id'], data['gateway'], float(data['value']),
                                                customer=customer)
        if transaction_status:
            customer.account_balance += data['value']
            customer.save()
            return Response({"result": "Balance successfully added to your account"}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_report_spam(request, pk):
    """
    post:
    Report user as spam
    """
    customer = get_object_or_404(Customer, pk=pk)
    reporter = get_object_or_404(Customer, user=request.user)

    try:
        if not SpamReport.objects.filter(customer=customer, reporter=reporter, verified=False).count():
            SpamReport.objects.create(customer=customer, reporter=reporter)
        return Response({"result": "successfully reported spam"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def interests_list(request):
    """
    get:
    List all the interests
    """
    interests = UserInterest.objects.all().order_by("-priority")
    serializer = UserInterestSerializer(interests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_interests(request):
    """
    get:
    List all the interests of user who made request
    patch:
    Update the list of interests of user who made request
    """
    customer = get_object_or_404(Customer.objects.prefetch_related('user_interests'), user=request.user)
    interests = customer.user_interests.all()

    if request.method == "GET":
        serializer = UserInterestSerializer(interests, many=True)
        return Response(serializer.data)

    elif request.method == "PATCH":
        data = [{'id': x} for x in request.data]
        serializer = UserInterestSerializer(interests, data=data, partial=True, many=True,
                                            context={'user': request.user})
        if serializer.is_valid():
            serializer.update(interests, data)
            add_articles_to_feed.delay(customer.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_education_list(request):
    """
    get:
    Get list of user's academics
    post:
    Add new school/college for user
    """
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == "GET":
        academics = Education.objects.filter(customer=customer).order_by("-from_year")
        serializer = EducationSerializer(academics, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        request.data['customer'] = customer.id
        serializer = EducationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_work_list(request):
    """
    get:
    Get list of user's occupation
    post:
    Add new workplace for user
    """
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == "GET":
        academics = Work.objects.filter(customer=customer).order_by("-from_year")
        serializer = WorkSerializer(academics, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        request.data['customer'] = customer.id
        serializer = WorkSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_education(request, pk):
    """
    get:
    Get education object by pk
    patch:
    Update education object details by pk
    delete:
    Delete education object by pk
    """
    education = get_object_or_404(Education, pk=pk)
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == 'GET':
        serializer = EducationSerializer(education)
        return Response(serializer.data)

    elif request.method == 'PATCH' and education.customer.user == request.user:
        serializer = EducationSerializer(education, data=request.data, partial=True)
        if serializer.is_valid():
            request.data['customer'] = customer
            serializer.update(education, request.data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE' and education.customer.user == request.user:
        education.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_work(request, pk):
    """
	get: 
	Get work object by pk
	patch: 
	Update work object details by pk
	delete: 
	Delete work object by pk
	"""
    work = get_object_or_404(Work, pk=pk)
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == 'GET':
        serializer = WorkSerializer(work)
        return Response(serializer.data)

    elif request.method == 'PATCH' and work.customer.user == request.user:
        serializer = WorkSerializer(work, data=request.data, partial=True)
        if serializer.is_valid():
            request.data['customer'] = customer
            serializer.update(work, request.data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE' and work.customer.user == request.user:
        work.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContactsSetPagination(PageNumberPagination):
    page_size = 30
    max_page_size = 100


@api_view(['GET', 'POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_contact_list(request):
    """
    get:
    Get list of user's contacts
    post:
    Add new contacts for user
    """
    customer = get_object_or_404(Customer, user=request.user)
    contacts = Contact.objects.filter(customer=customer)

    if request.method == "GET":
        paginator = ContactsSetPagination()
        contacts = paginator.paginate_queryset(contacts, request=request)
        serializer = ContactSerializer(contacts, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        final_data = []
        for row in request.data:
            row['phone_no'] = row['phone_no'].replace(' ', '')
            try:
                if not len(contacts.filter(phone_no=row['phone_no'])):
                    row['customer'] = customer.id
                    final_data.append(row)
                else:
                    contacts.filter(phone_no=row['phone_no']).update()
            except:
                pass

        serializer = ContactSerializer(data=final_data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(request.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', ])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def my_halanx_contacts_list(request):
    customer = get_object_or_404(Customer, user=request.user)
    halanx_customers = Customer.objects.filter(phone_no__in=Contact.objects.filter(customer=customer).
                                               values_list('phone_no', flat=True))
    paginator = StandardPagination()
    halanx_customers = paginator.paginate_queryset(halanx_customers, request=request)
    serializer = HalanxCustomerSerializer(halanx_customers, many=True, context={'customer': customer})
    return paginator.get_paginated_response(serializer.data)


class UsersSetPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_filter(request):
    customer = get_object_or_404(Customer, user=request.user)

    if not customer.is_visible:
        return Response({"error": "Set your visibility on to see other neighbors."},
                        status=status.HTTP_403_FORBIDDEN)

    q_lookup = []

    if 'name' in request.GET:
        name = request.GET['name']
        q_lookup.append(Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name))

    customers = Customer.objects.only('id').filter(is_visible=True, is_registered=True, *q_lookup).exclude(
        user=request.user)

    # filter by gender
    gender = request.GET.get('gender')
    if gender in ['Male', 'Female', 'Others']:
        customers = customers.filter(gender=gender)

    # filter by age
    from_age = request.GET.get('from_age')
    to_age = request.GET.get('to_age')
    if from_age and to_age:
        customers = list(filter(lambda c: int(from_age) <= c.age <= int(to_age), customers))

    customer_ids = [c.id for c in customers]

    # filter by distance
    radius = request.GET.get('radius')
    radius = int(radius) if radius else 5
    customers = Customer.objects.nearby(customer.clatitude, customer.clongitude, radius, ids=customer_ids)

    """
    # filter by interests
    my_interests = customer.user_interests.all()
    similar_customers = []
    for c, dis in filtered_customers:
        interests = c.user_interests.all()
        common = (my_interests & interests).count()
        similar_customers.append((c, dis, common))
    """

    customers = sorted(customers, key=lambda x: x[1])
    # prepare data
    distance_dict = {c[0].id: c[1] for c in customers}
    customers = [c[0] for c in customers]

    paginator = UsersSetPagination()
    customers = paginator.paginate_queryset(customers, request=request)
    serializer = UserProfileSerializer(customers, context={'distance': distance_dict, 'customer': customer}, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def user_fb_template_generator(request):
    customer = get_object_or_404(Customer, user=request.user)
    draw_template(customer)
    return Response({"img": customer.fb_template.url}, status=status.HTTP_200_OK)


# noinspection PyUnusedLocal,PyUnresolvedReferences
@api_view(['GET'])
def fbsharer(request, uid):
    try:
        uid = int(uid) // 191
        customer = Customer.objects.get(id=uid)
        img_url = customer.fb_template.url
        name = customer.user.first_name
    except Customer.DoesNotExist:
        img_url = None
        name = None

    return Response({"name": name, "img": img_url}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def user_ajax_filter(request):
    if request.method == 'GET':
        customers = list(Customer.objects.annotate(username=F('user__username'),
                                                   name=Concat('user__first_name', Value(' '), 'user__last_name'),
                                                   lat=F('clatitude'), lng=F('clongitude'),
                                                   pic=F('profile_pic_url')
                                                   ).values('id', 'username', 'name', 'phone_no', 'lat', 'lng',
                                                            'pic').all())
        return JsonResponse({'customers': customers})
    else:
        ids = [c['id'] for c in json.loads(request.data['customers'])]
        customers = Customer.objects.filter(id__in=ids)
        filtered_customers = []

        Type = request.data['type']

        if Type in ['post', 'order', 'subs', 'poll', 'title', 'group_order']:
            Min = int(request.data[Type + '_min'])
            Max = int(request.data[Type + '_max'])
            From = request.data[Type + '_from']
            To = request.data[Type + '_to']
            From = datetime.strptime(From, "%Y-%m-%d") if len(From) else datetime(2017, 9, 1)
            To = datetime.strptime(To, "%Y-%m-%d") if len(To) else datetime.now(pytz.timezone('Asia/Kolkata'))

        if Type == 'post':
            filtered_customers = customers.annotate(
                num_posts=Sum(Case(When(posts__timestamp__gte=From, posts__timestamp__lte=To, then=1),
                                   default=0, output_field=IntegerField()))
            ).filter(num_posts__gte=Min, num_posts__lte=Max)

        elif Type == 'order':
            filtered_customers = customers.annotate(
                num_orders=Sum(Case(When(orders__placing_time__gte=From, orders__placing_time__lte=To, then=1),
                                    default=0, output_field=IntegerField()))
            ).filter(num_orders__gte=Min, num_orders__lte=Max)

        elif Type == 'group_order':
            filtered_customers = customers.annotate(
                num_group_orders=Sum(Case(When(order__placing_time__gte=From, order__placing_time__lte=To,
                                               order__is_group_order=True, then=1), default=0,
                                          output_field=IntegerField()))
            ).filter(num_group_orders__gte=Min, num_group_orders__lte=Max)

        elif Type == 'subs':
            filtered_customers = customers.annotate(
                num_subs=Sum(Case(When(subscribeditem__timestamp__gte=From, subscribeditem__timestamp__lte=To,
                                       then=1), default=0, output_field=IntegerField()))
            ).filter(num_subs__gte=Min, num_subs__lte=Max)

        elif Type == 'poll':
            filtered_customers = customers.annotate(
                num_polls=Sum(Case(When(polls__timestamp__gte=From, polls__timestamp__lte=To, then=1),
                                   default=0, output_field=IntegerField()))
            ).filter(num_polls__gte=Min, num_polls__lte=Max)

        elif Type == 'title':
            filtered_customers = customers.annotate(
                num_titles=Sum(
                    Case(When(assigned_polls__timestamp__gte=From, assigned_polls__timestamp__lte=To, then=1),
                         default=0, output_field=IntegerField()))
            ).filter(num_titles__gte=Min, num_titles__lte=Max)

        elif Type == 'profile':
            data = request.data
            boolean_lookup = {'yes': True, 'no': False}
            myquery = Q()
            if data['is_registered'] != 'all':
                myquery &= Q(is_registered=boolean_lookup[data['is_registered']])
            if data['is_email_verified'] != 'all':
                myquery &= Q(is_verifiedEmail=boolean_lookup[data['is_email_verified']])

            From, To = request.data['last_visit_from'], request.data['last_visit_to']
            last_visit_from = datetime.strptime(From, "%Y-%m-%d") if len(From) else datetime(2017, 9, 1)
            last_visit_to = datetime.strptime(To, "%Y-%m-%d") if len(To) else timezone.now()
            myquery &= Q(last_visit__gte=last_visit_from, last_visit__lte=last_visit_to)
            myquery &= Q(profile_completion__gte=request.data['profile_min'],
                         profile_completion__lte=request.data['profile_max'])
            myquery &= Q(account_balance__gte=request.data['balance_min'],
                         account_balance__lte=request.data['balance_max'])
            myquery &= Q(hcash__gte=request.data['hcash_min'], hcash__lte=request.data['hcash_max'])

            filtered_customers = customers.filter(myquery)

            if len(request.data['location']):
                url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(
                    request.data['location'], config("GMAPS_DISTANCE_API_KEY"))
                data = requests.get(url).json()['results'][0]['geometry']['location']
                lat, lng = data['lat'], data['lng']
                radius = int(request.data['radius'])
                close_customers = []
                for c in filtered_customers:
                    try:
                        dis = find_distance((c.clatitude, c.clongitude), (lat, lng)).km
                        if int(dis) <= radius:
                            close_customers.append(c)
                    except:
                        pass
                filtered_customers = close_customers

        customers = []
        for customer in filtered_customers:
            row = {}
            row['id'] = customer.id
            row['username'] = customer.user.username
            row['name'] = customer.user.get_full_name()
            row['email'] = customer.user.email
            row['phone'] = customer.phone_no
            row['lat'] = customer.clatitude
            row['lng'] = customer.clongitude
            row['pic'] = customer.profile_pic_url
            customers.append(row)

        return JsonResponse({"customers": customers})


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_analytics(request):
    if not request.user.is_staff:
        return Response({"result": "You are not allowed to access this page!"}, status=status.HTTP_403_FORBIDDEN)

    notification_categories = list(zip(*NotificationCategories))[0]

    query_params = request.GET

    lat = float(query_params['lat']) if query_params.get('lat') else None
    lng = float(query_params['lng']) if query_params.get('lng') else None
    radius = float(query_params['radius']) if query_params.get('radius') else None

    if lat and lng and radius:
        nearby_customers = Customer.objects.nearby(lat, lng, radius)
        nearby_customer_ids = list(map(lambda x: x.id, list(zip(*nearby_customers))[0])) \
            if len(nearby_customers) else []
        customers = Customer.objects.filter(id__in=nearby_customer_ids)
    else:
        customers = Customer.objects.all()

    customers = customers.order_by(
        '-last_visit').annotate(username=F('user__username'),
                                name=Concat('user__first_name', Value(' '), 'user__last_name'),
                                lat=F('clatitude'), lng=F('clongitude'), pic=F('profile_pic_url')
                                ).values('id', 'username', 'name', 'phone_no', 'lat', 'lng', 'pic').all()

    customer_ids = list(customers.values_list('id', flat=True))
    paginator = Paginator(customers, 100)
    page = request.GET.get('page')
    try:
        customers = paginator.page(page)
    except PageNotAnInteger:
        customers = paginator.page(1)
    except EmptyPage:
        customers = paginator.page(paginator.num_pages)
    return render(request, 'customer_analytics1.html', {'gmapkey': config('GMAPS_JS_API_KEY'),
                                                        'customers': customers,
                                                        'customer_ids': customer_ids,
                                                        'is_paginated': True,
                                                        'notification_categories': notification_categories})


@api_view(['POST'])
def user_analytics_sms(request):
    if request.method == 'POST':
        customers = [c for c in json.loads(request.data['customers']) if c['select']]
        message = request.data['msg']
        mobiles = [str(c['phone']) for c in customers]

        url = config('MSG91_API_URL')
        authkey = config('MSG91_AUTH_KEY')
        sender = "halanx"

        if "$name" in message:
            for c in customers:
                values = {
                    'authkey': authkey,
                    'mobiles': c['phone'],
                    'message': message.replace("$name", c['name'].split()[0]) if len(c['name']) \
                        else message.replace("$name", c['phone']),
                    'sender': sender,
                    'route': "4"
                }
                _ = requests.post(url, data=values)

        else:
            values = {
                'authkey': authkey,
                'mobiles': ",".join(mobiles),
                'message': message,
                'sender': sender,
                'route': "4"
            }
            _ = requests.post(url, data=values)
        return JsonResponse({})


@shared_task
def send_notification(title, content, customer_ids):
    customers = Customer.objects.filter(id__in=customer_ids)
    for customer in customers:
        Notification(target=customer, category=ANNOUNCEMENT_NC).save({'title': title, 'content': content})


@api_view(['POST'])
def user_analytics_notification(request):
    if request.method == 'POST':
        customer_ids = json.loads(request.data.get('customer_ids'))
        title = request.data.get('title')
        content = request.data.get('content')
        send_notification.delay(title, content, customer_ids)
        return JsonResponse({})


@api_view(['POST'])
def user_analytics_email(request):
    if request.method == 'POST':
        ids = [c['id'] for c in json.loads(request.data['customers']) if c['select']]
        customers = Customer.objects.filter(id__in=ids)

        sg = sendgrid.SendGridAPIClient(apikey=config("SENDGRID_API_KEY"))
        from_email = Email("Halanx <support@halanx.com>")
        subject = request.data['subject']
        content = request.data['content']

        for customer in customers:
            if "$name" in content:
                pcontent = content.replace("$name", customer.user.first_name)
            else:
                pcontent = content
            to_email = Email(customer.user.email)
            mail = Mail(from_email, subject, to_email, Content("text/plain", pcontent))
            _ = sg.client.mail.send.post(request_body=mail.get())

        return JsonResponse({})


@api_view(['POST'])
def verify_otp(request):
    otp = get_object_or_404(OTP, phone_no=request.data.get('phone_no'), password=request.data.get('password'))
    if otp.timestamp <= timezone.now() - timedelta(minutes=4):
        return JsonResponse({'status': 'error', 'message': 'OTP Expired'})
    else:
        return JsonResponse({'status': 'success', 'message': 'OTP Verified'})


@api_view(['POST'])
def verify_email_otp(request):
    email_otp = get_object_or_404(EmailOTP, email=request.data.get('email'), password=request.data.get('password'))
    if email_otp.timestamp <= timezone.now() - timedelta(minutes=4):
        return JsonResponse({'status': 'error', 'message': 'OTP Expired'})
    else:
        return JsonResponse({'status': 'success', 'message': 'OTP Verified'})


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def link_social_account_with_already_registered_phone_no(request):
    required = ['phone_no', 'phone_otp']
    if not all([request.data.get(field) for field in required]):
        return Response({"error": "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate Phone OTP, this phone no belongs to google logged in user
    phone_otp = get_object_or_404(OTP, phone_no=request.data.get('phone_no'))

    if request.data.get('phone_otp') != phone_otp.password:
        return Response({"error": "Wrong OTP!"}, status=status.HTTP_400_BAD_REQUEST)

    if phone_otp.timestamp <= timezone.now() - timedelta(minutes=4):
        return JsonResponse({'status': 'error', 'message': 'OTP Expired'})

    customer = get_object_or_404(Customer, phone_no=request.data['phone_no'])
    # This customer and logged in google user are the same

    new_google_logged_in_user = request.user
    social_account = SocialAccount.objects.filter(provider__in=['facebook', 'google'], user=request.user).first()

    if social_account:
        email = social_account.extra_data.get('email', None)
        if email:
            email_address_obj = EmailAddress.objects.filter(email=email).first()

            if email_address_obj:
                email_address_obj.user = customer.user
                email_address_obj.verified = True
                email_address_obj.primary = True
                email_address_obj.save()

                social_account.user = customer.user
                social_account.save()

                registered_user = customer.user
                registered_user.email = email
                registered_user.save()

                # Delete created virtual user by google
                if registered_user != new_google_logged_in_user:
                    # important condition otherwise main user can get deleted if api called twice
                    new_google_logged_in_user.delete()

                key = Token.objects.get_or_create(user=registered_user)[0].key
                return Response({STATUS: SUCCESS, 'key': key})

    return Response({STATUS: ERROR}, status=status.HTTP_400_BAD_REQUEST)
