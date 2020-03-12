import json
import logging
import time
import urllib.parse
from hashlib import sha256, sha512

import requests
from decouple import config
from django.conf import settings

from utility import Checksum
from utility.environments import PRODUCTION
import razorpay

# Test
# RazorPayClient = razorpay.Client(auth=(config('RAZORPAY_TEST_SECRET'), config('RAZORPAY_TEST_KEY')))

# Live
RazorPayClient = razorpay.Client(auth=(config('RAZORPAY_LIVE_SECRET'), config('RAZORPAY_LIVE_KEY')))


RazorPayClient.set_app_details({"title": "Django", "version": "1.11"})


logger = logging.getLogger(__name__)

PAYU = 'PayU'
PAYTM = 'Paytm'
RAZORPAY = 'Razorpay'
FUND_TRANSFER = 'NEFT/IMPS'
CASH = 'Cash'
TOTAL_HCASH = 'TotalHcash'
PaymentGatewayChoices = (
    (PAYU, PAYU),
    (PAYTM, PAYTM),
    (FUND_TRANSFER, FUND_TRANSFER),
    (CASH, CASH),
    (RAZORPAY, RAZORPAY),
    (TOTAL_HCASH, TOTAL_HCASH)
)


def get_payu_transaction_id():
    """
    utility function to generate transaction id for payu
    """
    hash_object = sha256(str(int(time.time() * 1000)).encode('utf-8'))
    txnid = hash_object.hexdigest().lower()[0:32]
    return txnid


def generate_payu_hash_web(amount, first_name='', email='', phone='8506078226'):
    """
    utility function to generate payu hash for web
    hashSequence = 'key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10'
    """
    test = False
    if test:
        payu_url = config('PAYU_TEST_TRANSACTION_URL')
        payu_key = config('PAYU_TEST_KEY')
        payu_salt = config('PAYU_TEST_SALT')
    else:
        payu_url = config('PAYU_TRANSACTION_URL')
        payu_key = config('PAYU_KEY')
        payu_salt = config('PAYU_SALT')

    try:
        data = {
            'firstname': first_name,
            'email': email,
            'phone': phone,
            'amount': amount,
            'key': payu_key,
            'txnid': get_payu_transaction_id(),
            'service_provider': 'halanx',
            'action': payu_url,
            'productinfo': 'Halanx'
        }

        hash_string = payu_key + '|' + data['txnid'] + '|' + str(data['amount']) + '|' + data['productinfo']
        hash_string += '|' + data['firstname'] + '|' + data['email'] + '|'
        hash_string += '||||||||||' + payu_salt
        data['hash'] = sha512(hash_string.encode('utf-8')).hexdigest().lower()
        return data
    except Exception as e:
        logger.error("{} : {}".format(generate_payu_hash_web.__name__, e))


# noinspection PyPep8Naming
def generate_payu_hash_android(data):
    """
    utility function to generate payu hash for android
    sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT)
    """
    hash_keys = ('txnid', 'amount', 'productinfo', 'firstname', 'email', 'udf1', 'udf2', 'udf3', 'udf4', 'udf5')

    hashes = {}
    pkey = config('PAYU_KEY')
    salt = config('PAYU_SALT')

    value = pkey
    for key in hash_keys:
        value += "{}{}".format('|', data.get(key, ''))

    value += "{}{}".format('||||||', salt)
    hashes['payment_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    cmnNameMerchantCodes = 'get_merchant_ibibo_codes'
    value = pkey + '|' + cmnNameMerchantCodes + '|default|' + salt
    hashes['get_merchant_ibibo_codes_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    cmnMobileSdk = 'vas_for_mobile_sdk'
    value = pkey + '|' + cmnMobileSdk + '|default|' + salt
    hashes['vas_for_mobile_sdk_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    cmnEmiAmountAccordingToInterest = 'getEmiAmountAccordingToInterest'
    value = pkey + '|' + cmnEmiAmountAccordingToInterest + '|' + str(data.get('amount', '')) + '|' + salt
    hashes['emi_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    cmnPaymentRelatedDetailsForMobileSdk1 = 'payment_related_details_for_mobile_sdk'
    value = pkey + '|' + cmnPaymentRelatedDetailsForMobileSdk1 + '|default|' + salt
    hashes['payment_related_details_for_mobile_sdk_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    cmnVerifyPayment = 'verify_payment'
    value = pkey + '|' + cmnVerifyPayment + '|' + data.get('txnid', '') + '|' + salt
    hashes['verify_payment_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    if data.get('user_credentials'):
        cmnNameDeleteCard = 'delete_user_card'
        value = pkey + '|' + cmnNameDeleteCard + '|' + data['user_credentials'] + '|' + salt
        hashes['delete_user_card_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

        cmnNameGetUserCard = 'get_user_cards'
        value = pkey + '|' + cmnNameGetUserCard + '|' + data['user_credentials'] + '|' + salt
        hashes['get_user_cards_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

        cmnNameEditUserCard = 'edit_user_card'
        value = pkey + '|' + cmnNameEditUserCard + '|' + data['user_credentials'] + '|' + salt
        hashes['edit_user_card_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

        cmnNameSaveUserCard = 'save_user_card'
        value = pkey + '|' + cmnNameSaveUserCard + '|' + data['user_credentials'] + '|' + salt
        hashes['save_user_card_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

        cmnPaymentRelatedDetailsForMobileSdk = 'payment_related_details_for_mobile_sdk'
        value = pkey + '|' + cmnPaymentRelatedDetailsForMobileSdk + '|' + data['user_credentials'] + '|' + salt
        hashes['payment_related_details_for_mobile_sdk_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    if data.get('udf3'):
        cmnSend_Sms = 'send_sms'
        value = pkey + '|' + cmnSend_Sms + '|' + data['udf3'] + '|' + salt
        hashes['send_sms_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    if data.get('offerKey'):
        cmnCheckOfferStatus = 'check_offer_status'
        value = pkey + '|' + cmnCheckOfferStatus + '|' + data['offerKey'] + '|' + salt
        hashes['check_offer_status_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    if data.get('cardBin'):
        cmnCheckIsDomestic = 'check_isDomestic'
        value = pkey + '|' + cmnCheckIsDomestic + '|' + data['cardBin'] + '|' + salt
        hashes['check_isDomestic_hash'] = sha512(value.encode('utf-8')).hexdigest().lower()

    return hashes


def generate_paytm_hash_android(data):
    """
    utility function to generate paytm hash for android
    """
    logger.debug(data)
    response = {'CHECKSUMHASH': Checksum.generate_checksum(data, config('PAYTM_MERCHANT_KEY')),
                'ORDER_ID': data['ORDER_ID'],
                'payt_STATUS': 1}
    return response


def generate_razorpay_orderid_android(data, data_id):
    order_amount = round(data['TXN_AMOUNT'], 2)
    order_currency = 'INR'
    notes = {
        'data_id': data_id,
    }

    # Payment Capture 0 to validate amount etc
    order_create_dict = dict(amount=order_amount * 100,  # razorpay currency unit is paise
                             currency=order_currency,
                             notes=notes,
                             payment_capture='0')

    result = RazorPayClient.order.create(order_create_dict)
    razorpay_order_id = result['id']

    response = {
        'order_id': razorpay_order_id
    }
    return response


def get_paytm_transaction_status(order_id):
    """
    utility function to get paytm transaction status
    """
    data = {'MID': config('PAYTM_MERCHANT_ID'),
            'ORDERID': order_id}
    data['CHECKSUMHASH'] = urllib.parse.quote_plus(Checksum.generate_checksum(data, config('PAYTM_MERCHANT_KEY')))
    url = config('PAYTM_TRANSACTION_STATUS_URL')
    url += '?JsonData={"MID":"' + data['MID'] + '","ORDERID":"' + data['ORDERID'] + '","CHECKSUMHASH":"' + \
           data['CHECKSUMHASH'] + '"}'
    response_data = requests.get(url).json()
    logger.debug(json.dumps(response_data))
    return response_data.get('STATUS')


def get_payu_transaction_status(transaction_id):
    """
    utility function to get status of payu transaction
    """
    url = config('PAYU_TRANSACTION_VERIFICATION_URL')
    key = config('PAYU_KEY')
    salt = config('PAYU_SALT')
    if settings.ENVIRONMENT != PRODUCTION:
        url = config('PAYU_TEST_TRANSACTION_VERIFICATION_URL')
        key = config('PAYU_TEST_KEY')
        salt = config('PAYU_TEST_SALT')

    data = {
        'key': key,
        'salt': salt,
        'command': 'verify_payment',
        'var1': transaction_id
    }

    data['hash'] = '{}|{}|{}|{}'.format(data['key'], data['command'], data['var1'], data['salt'])
    data['hash'] = sha512(str(data['hash']).encode('utf-8')).hexdigest()

    res = requests.post(url, data=data, timeout=30)
    logger.debug(str(res.content))

    try:
        status = list(json.loads(res.content.decode('utf-8'))['transaction_details'].values())[0]['status']
    except Exception as e:
        logger.error(e)
        status = False
    return status


def get_razorpay_transaction_status(transaction_id):
    """
        utility function to get razorpay transaction status
    """
    global RazorPayClient
    return RazorPayClient.order.fetch(transaction_id)['status']


def verify_razorpay_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    param_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        RazorPayClient.utility.verify_payment_signature(param_dict)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def razorpay_capture_payment(razorpay_payment_id, amount):
    RazorPayClient.payment.capture(razorpay_payment_id, amount)
