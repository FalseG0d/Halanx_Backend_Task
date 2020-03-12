import logging
import re
from datetime import datetime

from django.apps import apps
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Sum
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import permission_classes, api_view, authentication_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (ListCreateAPIView, RetrieveUpdateAPIView, RetrieveDestroyAPIView,
                                     get_object_or_404, ListAPIView, UpdateAPIView, RetrieveAPIView, CreateAPIView,
                                     DestroyAPIView)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from Common.utils import CANCELLED, PAID, PENDING, ANDROID_PLATFORM
from Homes.AreaManagers.tasks import area_manager_cash_collection_notify
from Homes.Bookings.api.serializers import TenantTimeLineSerializer
from Homes.Bookings.models import Booking
from Homes.Bookings.utils import NEW_TENANT_BOOKING, EXISTING_TENANT_BOOKING
from Homes.Owners.api.serializers import BillSplitSerializer
from Homes.Houses.models import House, BillSplit
from Homes.Houses.utils import AVAILABLE, SHARED_ROOM
from Homes.Tenants.api.serializers import TenantSerializer, TenantDocumentSerializer, TenantPaymentSerializer, \
    TenantFavoriteHousesSerializer, TenantRequirementSerializer, TenantMoveOutRequestSerializer, TenantDetailSerializer, \
    TenantMealSerializer, TenantLateCheckInSerializer
from Homes.Tenants.models import Tenant, TenantDocument, TenantPayment, TenantWallet, TenantLateCheckin, TenantMeal, \
    TenantMoveOutRequest
from Homes.Tenants.utils import TENANT_REFERRED_CASHBACK_AMOUNT, get_cash_collection_time_slots, \
    CASH_COLLECTION_TIME_FORMAT, NEW_TENANT_UNREGISTERED_CUSTOMER, NEW_TENANT_REGISTERED_CUSTOMER, \
    EXISTING_TENANT_REGISTERED_CUSTOMER, EXISTING_TENANT_UNREGISTERED_CUSTOMER, BOOKING_PAYMENT
from Homes.permissions import IsTenant, IsOwner, IsTenantOrIsOwner
from Homes.utils import is_user_a_owner, is_user_a_tenant
from Notifications.models import Notification
from Notifications.utils import CASHBACK_NC
from Transaction.models import CustomerTransaction
from Transaction.utils import verify_transaction
from UserBase.models import Customer
from UserBase.serializers import UserSerializer
from utility.customer_utils import is_customer_exist
from utility.logging_utils import sentry_debug_logger
from utility.online_transaction_utils import CASH, FUND_TRANSFER, PAYTM, PAYU
from utility.online_transaction_utils import RAZORPAY, \
    verify_razorpay_payment_signature, razorpay_capture_payment
from utility.pagination_utils import StandardPagination
from utility.query_utils import get_filter_extra_kwargs
from utility.render_response_utils import STATUS, ERROR, SUCCESS
from utility.serializers import TimeSlotSerializer
from utility.logging_utils import sentry_debug_logger

logger = logging.getLogger(__name__)


class TenantRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        customer = get_object_or_404(Customer, user=self.request.user)
        tenant, _ = Tenant.objects.get_or_create(customer=customer)
        return tenant

    def partial_update(self, request, *args, **kwargs):
        tenant = self.get_object()
        customer = tenant.customer

        # Update Customer
        data = {}
        for field in ('dob',):  # add more if we want to update customer while updating tenant
            if request.data.get(field) is not None:
                data[field] = request.data[field]
        serializer = UserSerializer(customer, data=data, partial=True)
        if serializer.is_valid():
            if data.get('dob'):
                data['dob'] = datetime.strptime(data['dob'], "%d-%m-%Y").strftime('%Y-%m-%d')
                serializer.update(customer, data)

        # Update Tenant
        return super(TenantRetrieveUpdateView, self).partial_update(request, *args, **kwargs)


class TenantReferAndEarnView(APIView):
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    @staticmethod
    def post(request, **kwargs):
        tenant = get_object_or_404(Tenant, customer__user=request.user, referrer=None)
        referral_code = request.data.get('referral_code')
        friend = get_object_or_404(Tenant, tenant_referral_code=referral_code)

        if tenant != friend:
            tenant.referrer = friend
            tenant.save()
            tenant.customer.hcash += TENANT_REFERRED_CASHBACK_AMOUNT
            tenant.customer.save()

            # Sending Notification
            notification_payload = {'amount': TENANT_REFERRED_CASHBACK_AMOUNT}
            Notification(target=tenant.customer, category=CASHBACK_NC, payload=notification_payload).save(
                data={'amount': TENANT_REFERRED_CASHBACK_AMOUNT})
            return Response({'detail': 'Successfully availed cashback from refer & earn!'})

        else:
            if tenant == friend:
                return Response({'error': "You can't use your own referral code"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'You must have booked atleast one space'}, status=status.HTTP_400_BAD_REQUEST)


class TenantDocumentListCreateView(ListCreateAPIView):
    serializer_class = TenantDocumentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_queryset(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return tenant.documents.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        data = request.data
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(tenant=tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        categories = ['PAN', 'Employment', 'Aadhaar', 'Others']
        data = {}
        for category in categories:
            data[category] = self.get_serializer(queryset.filter(type=category), many=True).data
        return Response(data)


class TenantDocumentRetrieveDestroyView(RetrieveDestroyAPIView):
    serializer_class = TenantDocumentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return get_object_or_404(TenantDocument, tenant=tenant, pk=self.kwargs.get('pk'), is_deleted=False)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        document.is_deleted = True
        document.save()
        return Response({'detail': 'Successfully deleted document.'})


class TenantPaymentListView(ListAPIView):
    serializer_class = TenantPaymentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_queryset(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        queryset = tenant.wallet.payments.select_related('category').exclude(status=CANCELLED)
        payment_status = self.request.GET.get('status')
        if payment_status == PAID:
            return queryset.filter(status=payment_status).order_by('-paid_on')
        elif payment_status == PENDING:
            return queryset.filter(status=payment_status).order_by('due_date')
        else:
            return queryset


class TenantPaymentRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = TenantPaymentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        wallet = get_object_or_404(TenantWallet, tenant__customer__user=self.request.user)
        return get_object_or_404(TenantPayment.objects.prefetch_related('wallet__tenant__customer'),
                                 wallet=wallet, pk=self.kwargs.get('pk'), status=PENDING)

    def update(self, request, *args, **kwargs):
        payment = self.get_object()
        customer = payment.wallet.tenant.customer
        apply_cashback = request.data.get('apply_cashback')
        payment_gateway = request.data.get('payment_gateway')
        transaction_id = request.data.get('transaction_id')
        try:
            collection_time_start = datetime.strptime(request.data.get('collection_time_start'),
                                                      CASH_COLLECTION_TIME_FORMAT)
        except TypeError:
            collection_time_start = None

        if apply_cashback is not None:
            payment.apply_cashback = apply_cashback
            payment.save()

        elif payment_gateway in [CASH, FUND_TRANSFER]:
            payment.transaction = CustomerTransaction.objects.create(amount=payment.amount, customer=customer,
                                                                     transaction_id=transaction_id,
                                                                     platform=ANDROID_PLATFORM,
                                                                     payment_gateway=payment_gateway)
            if payment_gateway == CASH:
                area_manager = payment.booking.space.house.area_managers.first()
                if area_manager:
                    payment.transaction.collector = area_manager.user
                payment.transaction.collection_time_start = collection_time_start
                payment.transaction.save()
                payment.save()
                area_manager_cash_collection_notify.delay(payment.transaction.id)

        elif payment_gateway in [PAYTM, PAYU]:
            sentry_debug_logger.debug(payment_gateway + " gateway detected", exc_info=True)
            if verify_transaction(transaction_id, payment_gateway, payment.amount, customer=customer):
                payment.status = PAID
                payment.paid_on = timezone.now()
                payment.transaction = CustomerTransaction.objects.get(transaction_id=transaction_id, customer=customer,
                                                                      complete=True)

        elif payment_gateway in [RAZORPAY, ]:
            sentry_debug_logger.debug("Razor pay gateway detected", exc_info=True)

            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_signature = request.data.get('razorpay_signature')
            razorpay_order_id = transaction_id  # or order_id

            if razorpay_payment_id and razorpay_order_id and razorpay_signature:
                sentry_debug_logger.debug(
                    "Received all three razor pay params, now verifying signature and capturing payment",
                    exc_info=True)

                verified = verify_razorpay_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

                if verified:
                    sentry_debug_logger.debug("Signature verified, now capturing payment", exc_info=True)
                    # Capture amount when signature verified and amount matches
                    customer_transaction = CustomerTransaction.objects.get(transaction_id=transaction_id,
                                                                           customer=customer,
                                                                           payment_gateway=RAZORPAY)

                    if not customer_transaction.cancelled and not customer_transaction.complete:
                        if round(customer_transaction.amount, 2) == round(payment.amount, 2):
                            razorpay_capture_payment(razorpay_payment_id,
                                                     round((customer_transaction.amount * 100), 2))
                            sentry_debug_logger.debug('Amount captured Successfully', exc_info=True)
                        else:
                            sentry_debug_logger.debug('tenant payment amount mismatch with customer transaction amount')

                else:
                    sentry_debug_logger.debug("Signature not verifed")

            else:
                sentry_debug_logger.debug("Razorpay Params not found", exc_info=True)

            if verify_transaction(transaction_id, payment_gateway, payment.amount, customer=customer):
                payment.status = PAID
                payment.paid_on = timezone.now()
                payment.transaction = CustomerTransaction.objects.get(transaction_id=transaction_id, customer=customer,
                                                                      complete=True)
                payment.save()
                return Response({'status': 'success', 'message': 'Successfully paid'})

            else:
                return Response({'status': 'error', 'message': 'Payment not verified'},
                                status=status.HTTP_400_BAD_REQUEST)

        # elif payment_gateway in [TOTAL_HCASH, ] and True:  # UnTested
        #     sentry_debug_logger.debug(payment_gateway + " gateway detected", exc_info=True)
        #     sentry_debug_logger.debug(payment_gateway + "payment amount is " + str(payment.amount), exc_info=True)
        #     # If Transaction amount is 0 then create a transaction and pay directly as soon as
        #     #  gateway detected is TOTAL_HCASH
        #     if round(payment.amount, 2) == 0:
        #         payment.status = PAID
        #         payment.transaction = CustomerTransaction.objects.create(amount=payment.amount, customer=customer,
        #                                                                  platform=ANDROID_PLATFORM,
        #                                                                  payment_gateway=payment_gateway,
        #                                                                  )
        #
        #         payment.transaction.complete = True
        #         payment.transaction.save()
        #         payment.save()
        #
        #     else:
        #         return Response({'error': 'Invalid Transaction, Cant pay completely with HCASH'},
        #                         status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'error': 'Invalid transaction'}, status=status.HTTP_400_BAD_REQUEST)

        payment.save()
        serializer = self.get_serializer(payment)
        return Response(serializer.data)


class TenantPaymentBatchUpdateView(UpdateAPIView):
    serializer_class = TenantPaymentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def update(self, request, *args, **kwargs):
        wallet = get_object_or_404(TenantWallet, tenant__customer__user=request.user)
        customer = wallet.tenant.customer
        payment_ids = request.data.get('payments')
        payment_gateway = request.data.get('payment_gateway')
        transaction_id = request.data.get('transaction_id')
        try:
            collection_time_start = datetime.strptime(request.data.get('collection_time_start'),
                                                      CASH_COLLECTION_TIME_FORMAT)
        except TypeError:
            collection_time_start = None

        payments = TenantPayment.objects.prefetch_related('wallet__tenant__customer'). \
            filter(wallet=wallet, id__in=payment_ids, status=PENDING)
        total_amount = payments.aggregate(Sum('amount'))['amount__sum']

        if len(payments) is 0:
            return Response({'error': 'No payments found.'}, status=status.HTTP_400_BAD_REQUEST)

        if payment_gateway in [CASH, FUND_TRANSFER]:
            transaction = CustomerTransaction.objects.create(amount=total_amount, customer=customer,
                                                             transaction_id=transaction_id, platform=ANDROID_PLATFORM,
                                                             payment_gateway=payment_gateway)
            if payment_gateway == CASH:
                area_manager = payments.first().booking.space.house.area_managers.first()
                if area_manager:
                    transaction.collector = area_manager.user
                transaction.collection_time_start = collection_time_start
                transaction.save()
            # save one by one to call signals
            for payment in payments:
                payment.transaction = transaction
                payment.save()

            if payment_gateway == CASH:
                area_manager_cash_collection_notify.delay(transaction.id)

        elif payment_gateway in [PAYTM, PAYU]:
            if verify_transaction(transaction_id, payment_gateway, total_amount, customer=customer):
                transaction = CustomerTransaction.objects.get(transaction_id=transaction_id, customer=customer,
                                                              complete=True)
                # save one by one to call signals
                for payment in payments:
                    payment.status = PAID
                    payment.paid_on = timezone.now()
                    payment.transaction = transaction
                    payment.save()

        elif payment_gateway in [RAZORPAY, ]:
            sentry_debug_logger.debug("Razor pay gateway detected", exc_info=True,
                                      extra={'tags': {'TenantPaymentBatch': {}}})

            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_signature = request.data.get('razorpay_signature')
            razorpay_order_id = transaction_id  # or order_id

            if razorpay_payment_id and razorpay_order_id and razorpay_signature:
                sentry_debug_logger.debug(
                    "Received all three razor pay params, now verifying signature and capturing payment",
                    exc_info=True, extra={'tags': {'TenantPaymentBatch': {}}})

                verified = verify_razorpay_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

                if verified:
                    sentry_debug_logger.debug("Signature verified, now capturing payment", exc_info=True,
                                              extra={'tags': {'TenantPaymentBatch': {}}})
                    # Capture amount when signature verified and amount matches
                    customer_transaction = CustomerTransaction.objects.get(transaction_id=transaction_id,
                                                                           customer=customer,
                                                                           payment_gateway=RAZORPAY)

                    if not customer_transaction.cancelled and not customer_transaction.complete:
                        if round(customer_transaction.amount, 2) == round(total_amount, 2):
                            razorpay_capture_payment(razorpay_payment_id, round((customer_transaction.amount * 100), 2))
                            sentry_debug_logger.debug('Amount captured Succesfully', exc_info=True,
                                                      extra={'tags': {'TenantPaymentBatch': {}}})
                        else:
                            sentry_debug_logger.debug('tenant payment amount mismatch with customer transaction amount',
                                                      extra={'tags': {'TenantPaymentBatch': {}}})
                else:
                    sentry_debug_logger.debug("Signature not verified", extra={'tags': {'TenantPaymentBatch': {}}})
            else:
                sentry_debug_logger.debug("Razorpay Params not found", exc_info=True,
                                          extra={'tags': {'TenantPaymentBatch': {}}})

            if verify_transaction(transaction_id, payment_gateway, total_amount, customer=customer):
                sentry_debug_logger.debug("Transaction verified", exc_info=True,
                                          extra={'tags': {'TenantPaymentBatch': {}}})

                transaction = CustomerTransaction.objects.get(transaction_id=transaction_id, customer=customer,
                                                              complete=True)
                # save one by one to call signals
                for payment in payments:
                    payment.status = PAID
                    payment.paid_on = timezone.now()
                    payment.transaction = transaction
                    payment.save()

                return Response({STATUS: SUCCESS, 'message': 'Successfully paid'})
            else:
                return Response({STATUS: ERROR, 'message': 'Payment not verified'},
                                status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'error': 'Invalid transaction'}, status=status.HTTP_400_BAD_REQUEST)
        logger.debug(str(payments))
        return Response({'result': 'Successfully patched!'})


class TenantPaymentCashCollectionTimeSlotsRetrieveView(RetrieveAPIView):
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def retrieve(self, request, *args, **kwargs):
        wallet = get_object_or_404(TenantWallet, tenant__customer__user=self.request.user)
        payment = get_object_or_404(TenantPayment.objects.prefetch_related('wallet__tenant__customer'),
                                    wallet=wallet, pk=self.kwargs.get('pk'), status=PENDING)
        time_slots = get_cash_collection_time_slots(payment)
        data = self.get_serializer(time_slots, many=True).data
        return Response(data)


class TenantFavoriteHousesListView(ListAPIView):
    serializer_class = TenantFavoriteHousesSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_queryset(self):
        tenant = get_object_or_404(Tenant.objects.prefetch_related('favorite_houses'), customer__user=self.request.user)
        return tenant.favorite_houses.all()


class TenantRequirementCreateView(CreateAPIView):
    serializer_class = TenantRequirementSerializer
    permission_classes = [AllowAny, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            tenant = Tenant.objects.get(customer__user=self.request.user)
        except (Tenant.DoesNotExist, TypeError):
            tenant = None

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(tenant=tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TenantMoveOutRequestCreateView(CreateAPIView):
    serializer_class = TenantMoveOutRequestSerializer
    queryset = TenantMoveOutRequest.objects.all()
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    def __init__(self, *args, **kwargs):
        super(TenantMoveOutRequestCreateView, self).__init__(*args, **kwargs)
        self.tenant = None

    def post(self, request, *args, **kwargs):
        self.tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        request.data['tenant'] = self.tenant.id
        return super(TenantMoveOutRequestCreateView, self).post(request, *args, **kwargs)


# class TenantMoveInRequestCreateView(CreateAPIView):
#     serializer_class = TenantMoveInRequestSerializer
#     queryset = TenantMoveInRequest.objects.all()
#     authentication_classes = (BasicAuthentication, TokenAuthentication)
#     permission_classes = (IsAuthenticated,)
#
#     def __init__(self, *args, **kwargs):
#         super(TenantMoveInRequestCreateView, self).__init__(*args, **kwargs)
#         self.tenant = None
#
#     def post(self, request, *args, **kwargs):
#         self.tenant = get_object_or_404(Tenant, customer__user=self.request.user)
#         request.data['tenant'] = self.tenant.id
#         return super(TenantMoveInRequestCreateView, self).post(request, *args, **kwargs)

class TenantListView(ListAPIView):
    """
     get: Lists all the tenants added by the logged in owner,
     post: Creates a new Tenant
    """
    permission_classes = [IsOwner, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_queryset(self):
        owner = is_user_a_owner(request=self.request, raise_exception=True)
        return Tenant.objects.filter(bookings__space__house__owner=owner)

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        if self.request.method == "GET":
            kwargs['display_fields'] = ['id', 'customer', 'permanent_address', 'parent_name', 'parent_phone_no',
                                        'current_stay']
            return TenantDetailSerializer(*args, **kwargs)


def send_notification_to_tenant(phone_no, title, customer):
    print("Send notification to the tenant with title", title)


def validate_phone_no_space_and_free_beds(request, owner):
    if len(request.data['phone_no']) < 10:
        raise ValidationError({'detail': 'phone_no must have length atleast 10'})

    # check if space actually exists
    try:
        from Homes.Houses.models import Space
        space = get_object_or_404(Space, pk=request.data['space'],
                                  house__owner=owner,
                                  availability=AVAILABLE)
    except Http404:
        raise ValidationError({'detail': "Space doesn't exists"})

    if space.type == SHARED_ROOM:
        free_bed = space.shared_room.beds.filter(availability=AVAILABLE, visible=True)
        if not free_bed:
            raise ValidationError({'detail': "No free bed exists"})

    return request.data['phone_no'], space


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsOwner,))
def create_tenant_view(request):
    """
    1. validation phone and space data
    """
    owner = is_user_a_owner(request, raise_exception=True)
    # Phone no, name, space, rent are mandatory
    required = ('phone_no', 'space', 'rent', 'license_start_date')

    if not all(request.data.get(field) for field in required):
        return Response({'error': "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)

    phone_no, space = validate_phone_no_space_and_free_beds(request=request, owner=owner)  # validate phone_no and space
    if request.data.get('name', None):
        name = request.data['name']
    else:
        name = ''

    # extract phone number
    phone_no = re.sub(r'\+91|[-\s()]', '', request.data['phone_no'])

    customer = is_customer_exist(phone_no)

    if customer is None:  # if No such customer exists create user
        try:
            user, created = User.objects.get_or_create(username="c{}".format(phone_no),
                                                       password="p{}".format(phone_no),
                                                       )
            if created:
                user.first_name = name
                user.save()

        except IntegrityError:  # user already exists
            user = User.objects.get(username="c{}".format(phone_no))

        customer_create_data = dict(user=user, phone_no=phone_no, is_registered=False)
        customer = Customer.objects.create(**customer_create_data)

    tenant, created = Tenant.objects.get_or_create(customer=customer)
    notification_message = ""
    if created:
        tenant_type_booking = NEW_TENANT_BOOKING
    else:
        tenant_type_booking = EXISTING_TENANT_BOOKING

    if created and customer.is_registered:  # New Tenant created and the customer is already registered on Halanx
        notification_message = NEW_TENANT_REGISTERED_CUSTOMER
    elif created and not customer.is_registered:  # New Tenant created and the customer is not registered on Halanx
        notification_message = NEW_TENANT_UNREGISTERED_CUSTOMER
    elif not created:
        if tenant.current_booking is not None:
            raise ValidationError({'detail': "This tenant already has current booking"})
        if tenant.customer.is_registered:  # Tenant already exists
            notification_message = EXISTING_TENANT_REGISTERED_CUSTOMER
        if not tenant.customer.is_registered:
            notification_message = EXISTING_TENANT_UNREGISTERED_CUSTOMER

    send_notification_to_tenant(phone_no=phone_no, customer=customer, title=notification_message)

    booking_creation_data = {
        'space': space, 'tenant': tenant, 'type': tenant_type_booking, 'rent': request.data['rent'],
        'license_start_date': request.data['license_start_date']
    }

    extra_fields = ('security_deposit', 'token_amount', 'onboarding_charges', 'paid_token_amount',
                    'paid_movein_charges', 'move_in_notes')

    for field in extra_fields:
        if request.data.get(field, None):
            booking_creation_data[field] = request.data.get(field)

    Booking.objects.create(**booking_creation_data)

    tenant_data = TenantDetailSerializer(tenant, display_fields=['id', 'customer']).data

    response_data = {
        'status': 'success',
        'data': tenant_data
    }
    return Response(response_data, status=status.HTTP_201_CREATED)


class TenantLateCheckinListCreateView(ListCreateAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        # returns all the check-ins of every current booking of spaces where space house owner = logged in owner
        owner = is_user_a_owner(self.request, raise_exception=False)
        if owner:
            return TenantLateCheckin.objects.filter(current_booking__space__house__owner=owner)

        # returns all the check-ins of logged in tenant
        tenant = is_user_a_tenant(self.request, raise_exception=True)
        if tenant:
            return TenantLateCheckin.objects.filter(current_booking=tenant.current_booking)

    def create(self, request, *args, **kwargs):
        tenant = is_user_a_tenant(request, raise_exception=False)
        booking = get_object_or_404(Booking,
                                    tenant=tenant,
                                    moved_out=False)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer=serializer, booking=booking)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # noinspection PyMethodOverriding
    def perform_create(self, serializer, booking: Booking):
        serializer.save(current_booking=booking)

    def get_serializer_class(self):
        return TenantLateCheckInSerializer


class TenantLateCheckinDestroyView(DestroyAPIView):
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsTenant,)

    def get_object(self):
        tenant = is_user_a_tenant(request=self.request, raise_exception=True)
        return get_object_or_404(TenantLateCheckin, current_booking__tenant=tenant, pk=self.kwargs.get('pk'))


class TenantMealListCreateView(ListCreateAPIView):
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsTenantOrIsOwner,)

    def get_queryset(self):
        owner = is_user_a_owner(self.request, raise_exception=False)
        if owner:
            return TenantMeal.objects.filter(house__owner=owner)

        tenant = is_user_a_tenant(self.request, raise_exception=False)
        if tenant:
            return TenantMeal.objects.filter(house=tenant.current_booking.space.house)

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        if is_user_a_tenant(self.request, raise_exception=False):
            kwargs['exclude_fields'] = ('having',)
            return TenantMealSerializer(*args, **kwargs)
        else:
            return TenantMealSerializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        owner = is_user_a_owner(request, raise_exception=True)
        get_object_or_404(House, owner=owner, id=request.data['house'])
        return super(TenantMealListCreateView, self).create(request, *args, **kwargs)


@permission_classes((IsTenant,))
@authentication_classes((BasicAuthentication, TokenAuthentication))
@api_view(('POST',))
def tenant_accept_meal(request):
    tenant = is_user_a_tenant(request, raise_exception=True)
    required = ('meal',)
    if not all(request.data.get(field) for field in required):
        return Response({'error': "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)

    if tenant.current_booking.space.house.meals.filter(id=request.data['meal']):
        TenantMeal.objects.get(id=request.data['meal']).accepted_by.add(tenant)
        return Response({'status': 'success', 'message': 'Meal Accepted'}, status=status.HTTP_202_ACCEPTED)

    else:
        return Response({'status': 'error', 'message': "meal does not exist"}, status=status.HTTP_202_ACCEPTED)


class TenantBillListView(ListAPIView):
    permission_classes = (IsTenant,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    pagination_class = StandardPagination

    def get_queryset(self):
        tenant = is_user_a_tenant(self.request, raise_exception=True)
        query_filter_params = {
            'paid': 'paid',
            'due_date__lte': 'due_date__lte',
            'due_date__gte': 'due_date__gte',
            'amount__lte': 'amount__lte',
            'amount__gte': 'amount__gte'
        }

        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request)
        return BillSplit.objects.filter(tenant=tenant, **extra_kwargs)

    def get_serializer_class(self):
        return BillSplitSerializer


class TenantTimeLineView(RetrieveAPIView):
    permission_classes = (IsOwner,)
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def __init__(self):
        super(TenantTimeLineView, self).__init__()
        self.owner = None

    def get(self, request, *args, **kwargs):
        self.owner = is_user_a_owner(request=request, raise_exception=True)
        if self.owner:
            tenant = get_object_or_404(Tenant, pk=request.query_params['tenant'])
            return Response(self.get_serializer(tenant).data, status=status.HTTP_200_OK)

    def get_serializer_context(self):
        context = super(TenantTimeLineView, self).get_serializer_context()
        context['owner'] = self.owner
        return context

    def get_serializer_class(self):
        return TenantTimeLineSerializer


class TenantRetrieveView(RetrieveAPIView):
    permission_classes = [IsOwner, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        owner = is_user_a_owner(self.request, raise_exception=True)
        tenant = get_object_or_404(Tenant, pk=self.kwargs.get('pk'))
        try:
            if tenant.current_booking.space.house.owner == owner:
                return tenant
        except:
            raise Http404({'detail': "Tenant does not have any booking in your house"})

    def get_serializer_class(self):
        return TenantDetailSerializer
