from random import randint

from rest_framework.generics import get_object_or_404

from Notifications.models import Notification
from Notifications.utils import CASHBACK_NC

GenderChoices = (
    ("male", "Male"),
    ("female", "Female"),
    ("other", "Other"),
)

RelationshipStatusChoices = (
    ("Single", "Single"),
    ("In a relationship", "In a relationship"),
    ("Engaged", "Engaged"),
    ("Married", "Married"),
    ("Divorced", "Divorced"),
    ("Widowed", "Widowed"),
    ("Separated", "Separated"),
    ("It's complicated", "It's complicated"),
)

profile_completion_fields = ('gender', 'bio', 'dob', 'address', 'relationship_status', 'is_email_verified')

default_profile_pic_url = "https://d28fujbigzf56k.cloudfront.net/static/img/nopic.jpg"
default_profile_pic_thumbnail_url = "https://d28fujbigzf56k.cloudfront.net/static/img/nopic_small.jpg"

FB_PROFILE_PIC_URL = "http://graph.facebook.com/{}/picture?type=large"

CUSTOMER_UPDATABLE_FIELDS = ("address", "relationship_status", "dob", "gender", "bio", "receive_notification",
                             "email", "is_visible", "dlatitude", "dlongitude", "clatitude", "clongitude", "gcm_id",
                             "first_name", "last_name", "campaign")

HALANX_SUPPORT_USERNAME = 'c9999999999'
HALANX_SUPPORT_MESSAGE_ON_CUSTOMER_REGISTER = 'Hi , I am Halanx Support. How can I help you'


def get_picture_upload_path(instance, filename):
    return "customers/{}/pictures/{}_{}".format(instance.customer.id, randint(111111, 999999), filename.split('/')[-1])


def get_thumbnail_upload_path(instance, filename):
    return "customers/{}/thumbnail/{}_{}".format(instance.customer.id, randint(111111, 999999), filename.split('/')[-1])


def get_fb_template_upload_path(instance, filename):
    return "customers/{}/fbshare/{}_{}".format(instance.id, randint(111111, 999999), filename.split('/')[-1])


def generate_customer_referral_code(user):
    return ((user.first_name.capitalize() if len(user.first_name) else 'Halanx') +
            (user.last_name[0].upper() if len(user.last_name) else 'R') + str(user.id))


def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


CUSTOMER_REFERRAL = 'customer'
TENANT_REFERRAL = 'tenant'

CUSTOMER_REFERRED_CASHBACK_AMOUNT = 50
CUSTOMER_REFERRER_CASHBACK_AMOUNT = 50


def get_referral_code_type(code):
    if is_int(code.split('t')[-1]):
        return TENANT_REFERRAL
    return CUSTOMER_REFERRAL


def avail_customer_refer_and_earn(customer, referral_code):
    """
    Avail customer refer & earn by entering referral code of a friend and having no orders or existing referrer.
    """
    from UserBase.models import Customer
    friend = get_object_or_404(Customer, referral_code=referral_code)
    if customer != friend and not customer.orders.count() and customer.referrer is None:
        customer.referrer = friend
        customer.hcash += CUSTOMER_REFERRED_CASHBACK_AMOUNT
        customer.save()
        notification_payload = {'amount': CUSTOMER_REFERRED_CASHBACK_AMOUNT}
        Notification(target=customer, category=CASHBACK_NC, payload=notification_payload).save(
            data={"amount": CUSTOMER_REFERRED_CASHBACK_AMOUNT})
        return True
