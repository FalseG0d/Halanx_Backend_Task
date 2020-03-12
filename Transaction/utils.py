from random import randint

from Homes.Owners.models import Owner
from StoreBase.models import Store
from UserBase.models import Customer
from utility.logging_utils import sentry_debug_logger
from utility.online_transaction_utils import PAYU, PAYTM, get_payu_transaction_status, get_paytm_transaction_status, \
    RAZORPAY, get_razorpay_transaction_status
from typing import Union


def get_deposit_reference_image_upload_path(instance, filename):
    return "Transactions/Cash-Deposit/{}/{}_{}".format(instance.collector.id, randint(111111, 999999),
                                                       filename.split('/')[-1])


def get_transaction_status(transaction):
    """
    Utility function to get status of a transaction object
    """
    if transaction.payment_gateway == PAYU:
        return get_payu_transaction_status(transaction.transaction_id) == 'success'
    elif transaction.payment_gateway == PAYTM:
        return get_paytm_transaction_status(transaction.transaction_id) == 'TXN_SUCCESS'
    elif transaction.payment_gateway == RAZORPAY:
        return get_razorpay_transaction_status(transaction.transaction_id) == 'paid'

    else:
        return False


def verify_transaction(transaction_id: str, gateway: str, amount: float,
                       account_type: Union['customer', 'store', 'house_owner'] = 'customer', customer: Customer = None,
                       store: Store = None, owner: Owner = None) -> bool:
    """
    utility function to verify transaction by id
    """
    amount = round(amount, 2)
    if account_type == 'customer':
        from Transaction.models import CustomerTransaction
        transaction = CustomerTransaction.objects.filter(transaction_id=transaction_id, amount=amount,
                                                         customer=customer, payment_gateway=gateway,
                                                         complete=False).first()
    elif account_type == 'store':
        from Transaction.models import StoreTransaction
        transaction = StoreTransaction.objects.filter(transaction_id=transaction_id, store=store, amount=amount,
                                                      payment_gateway=gateway, complete=False).first()
    elif account_type == 'house_owner':
        from Transaction.models import HouseOwnerTransaction
        transaction = HouseOwnerTransaction.objects.filter(transaction_id=transaction_id, owner=owner, amount=amount,
                                                           payment_gateway=gateway, complete=False).first()
    else:
        transaction = None

    if transaction:
        transaction.complete = get_transaction_status(transaction)
        transaction.save()
        return round(float(transaction.amount), 2) == round(amount, 2) and transaction.complete
    else:
        return False
