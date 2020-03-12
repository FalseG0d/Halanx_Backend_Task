from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from Common.utils import ANDROID_PLATFORM, WEB_PLATFORM
from Homes.Owners.models import Owner
from StoreBase.models import Store
from Transaction.models import StoreTransaction, HouseOwnerTransaction, CustomerTransaction
from UserBase.models import Customer
from utility.online_transaction_utils import (generate_payu_hash_web, generate_payu_hash_android,
                                              generate_paytm_hash_android,
                                              PAYU, PAYTM, generate_razorpay_orderid_android, RAZORPAY)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def generate_paytm_hash_view_android(request):
    data = request.data
    account_type = request.GET.get('account_type', 'customer')

    if account_type == 'customer':
        customer = get_object_or_404(Customer, user=request.user)
        response = generate_paytm_hash_android(data)
        CustomerTransaction.objects.create(transaction_id=data.get('ORDER_ID'), customer=customer,
                                           amount=data.get("TXN_AMOUNT"), payment_gateway=PAYTM,
                                           platform=ANDROID_PLATFORM)
    elif account_type == 'store':
        store = get_object_or_404(Store, user=request.user)
        response = generate_paytm_hash_android(data)
        StoreTransaction.objects.create(transaction_id=data.get('ORDER_ID'), store=store, amount=data.get("TXN_AMOUNT"),
                                        payment_gateway=PAYTM, platform=ANDROID_PLATFORM)
    elif account_type == 'house_owner':
        owner = get_object_or_404(Owner, user=request.user)
        response = generate_paytm_hash_android(data)
        HouseOwnerTransaction.objects.create(transaction_id=data.get('ORDER_ID'), store=owner,
                                             amount=data.get("TXN_AMOUNT"), payment_gateway=PAYTM,
                                             platform=ANDROID_PLATFORM)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(response)


@api_view(['POST'])
def generate_payu_hash_view_android(request, pk):
    data = request.data
    account_type = request.GET.get('account_type', 'customer')

    if account_type == 'customer':
        customer = get_object_or_404(Customer, pk=pk)
        hashes = generate_payu_hash_android(data)
        CustomerTransaction.objects.create(transaction_id=data.get('txnid'), customer=customer,
                                           amount=data.get('amount'), payment_gateway=PAYU, platform=ANDROID_PLATFORM)

    elif account_type == 'store':
        store = get_object_or_404(Store, pk=pk)
        hashes = generate_payu_hash_android(data)
        StoreTransaction.objects.create(transaction_id=data.get('txnid'), store=store, amount=data.get('amount'),
                                        payment_gateway=PAYTM, platform=ANDROID_PLATFORM)

    elif account_type == 'house_owner':
        owner = get_object_or_404(Owner, pk=pk)
        hashes = generate_payu_hash_android(data)
        HouseOwnerTransaction.objects.create(transaction_id=data.get('txnid'), owner=owner, amount=data.get('amount'),
                                             payment_gateway=PAYTM, platform=ANDROID_PLATFORM)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(hashes)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def generate_payu_hash_view_web(request):
    try:
        amount = float(request.data.get('amount'))
    except Exception as e:
        return Response({'error': e}, status=status.HTTP_400_BAD_REQUEST)
    account_type = request.data.get('account_type', 'customer')

    if account_type == 'customer':
        customer = get_object_or_404(Customer, user=request.user)
        data = generate_payu_hash_web(amount, first_name=customer.user.first_name, email=customer.user.email,
                                      phone=customer.phone_no)
        CustomerTransaction.objects.create(transaction_id=data.get('txnid'), customer=customer,
                                           amount=data.get('amount'), payment_gateway=PAYU, platform=WEB_PLATFORM)

    elif account_type == 'store':
        store = get_object_or_404(Store, user=request.user)
        data = generate_payu_hash_web(amount, first_name=store.user.first_name, email=store.user.email)
        StoreTransaction.objects.create(transaction_id=data.get('txnid'), store=store, amount=data.get('amount'),
                                        payment_gateway=PAYU, platform=WEB_PLATFORM)

    elif account_type == 'house_owner':
        owner = get_object_or_404(Owner, user=request.user)
        data = generate_payu_hash_web(amount, first_name=owner.user.first_name, email=owner.user.email)
        HouseOwnerTransaction.objects.create(transaction_id=data.get('txnid'), owner=owner, amount=data.get('amount'),
                                             payment_gateway=PAYU, platform=WEB_PLATFORM)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def generate_razorpay_orderid_view_android(request):
    data = request.data
    account_type = request.GET.get('account_type', 'customer')

    if account_type == 'customer':
        customer = get_object_or_404(Customer, user=request.user)
        response = generate_razorpay_orderid_android(data, customer.id)
        CustomerTransaction.objects.create(transaction_id=response['order_id'], customer=customer,
                                           amount=data.get("TXN_AMOUNT"), payment_gateway=RAZORPAY,
                                           platform=ANDROID_PLATFORM)

    elif account_type == 'store':
        store = get_object_or_404(Store, user=request.user)
        response = generate_razorpay_orderid_android(data, store.id)
        StoreTransaction.objects.create(transaction_id=response['order_id'], store=store, amount=data.get("TXN_AMOUNT"),
                                        payment_gateway=RAZORPAY, platform=ANDROID_PLATFORM)

    elif account_type == 'house_owner':
        owner = get_object_or_404(Owner, user=request.user)
        response = generate_razorpay_orderid_android(data, owner.id)
        HouseOwnerTransaction.objects.create(transaction_id=response['order_id'], owner=owner,
                                             amount=data.get("TXN_AMOUNT"), payment_gateway=RAZORPAY,
                                             platform=ANDROID_PLATFORM)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(response)