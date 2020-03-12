from datetime import timedelta, datetime, time
from random import randint

from django.utils import timezone
from rest_framework.generics import get_object_or_404

from Notifications.models import Notification
from Notifications.utils import CASHBACK_NC

MOVE_OUT = 'Move Out'
# Tenant Meal

BREAKFAST = 'breakfast'
LUNCH = 'lunch'
DINNER = 'dinner'

MEAL_TYPES = (
    (BREAKFAST, 'Breakast'),
    (LUNCH, 'Lunch'),
    (DINNER, 'Dinner'),
)

NEW_TENANT_REGISTERED_CUSTOMER = "You were added by {owner_name} at FreeOwner App. See now"
NEW_TENANT_UNREGISTERED_CUSTOMER = "Register at FreeOwner App. {owner_name} added you on FreeOwner"
EXISTING_TENANT_REGISTERED_CUSTOMER = "You were added by {owner_name} at FreeOwner App. See now"
EXISTING_TENANT_UNREGISTERED_CUSTOMER = "Register at FreeOwner App. {owner_name} added you on FreeOwner"


def get_tenant_document_upload_path(instance, filename):
    return "Tenants/{}/documents/{}/{}_{}".format(instance.tenant.id, instance.type, randint(111111, 999999),
                                                  filename.split('/')[-1])


def get_tenant_document_thumbnail_upload_path(instance, filename):
    return "Tenants/{}/documents/{}/thumbnail/{}_{}".format(instance.tenant.id, instance.type, randint(111111, 999999),
                                                            filename.split('/')[-1])


def generate_tenant_referral_code(tenant):
    user = tenant.customer.user
    return ((user.first_name.capitalize() if len(user.first_name) else 'Halanx') +
            (user.last_name[0].upper() if len(user.last_name) else 'H') + 't' + str(tenant.id))


def generate_owner_referral_code(tenant):
    user = tenant.customer.user
    return ((user.first_name.capitalize() if len(user.first_name) else 'Halanx') +
            (user.last_name[0].upper() if len(user.last_name) else 'H') + 'o' + str(tenant.id))


# Tenant payment category choices
REFUND_PAYMENT = "Refund"
MONTHLY_RENT_PAYMENT = "Monthly Rent"
BOOKING_PAYMENT = "Booking"
MOVEIN_PAYMENT = "Move-In"
SERVICE_REQUEST_PAYMENT = "Service Request"

# Tenant payment descriptions
BOOKING_PAYMENT_DESCRIPTION = "Token amount to book your new home"
MOVEIN_PAYMENT_DESCRIPTION = "Move-In charges for your new home"
MONTHLY_RENT_PAYMENT_DESCRIPTION = "Monthly rent for {} to {}"

SUCCESSFUL_TENANT_PAYMENT_MSG = "Hi {}! Your payment of {} of Rs.{} via {} was successful. Payment ID:-{}\nThank You."

# refer and earn cashbacks
TENANT_REFERRED_CASHBACK_AMOUNT = 200
TENANT_REFERRER_CASHBACK_AMOUNT = 200

# hcash limit
TENANT_PAYMENT_HCASH_LIMIT_PERCENTAGE = 0.2

CASH_COLLECTION_TIME_FORMAT = '%d %B %Y %I:%M %p'


def avail_tenant_refer_and_earn(customer, referral_code):
    """
    Avail tenant refer & earn by entering referral code of a friend and having no booking or existing referrer.
    """
    from Homes.Tenants.models import Tenant
    tenant = get_object_or_404(Tenant, customer=customer, referrer=None)
    friend = get_object_or_404(Tenant, tenant_referral_code=referral_code)

    if tenant != friend and not tenant.bookings.count() and tenant.referrer is None:
        tenant.referrer = friend
        tenant.save()
        tenant.customer.hcash += TENANT_REFERRED_CASHBACK_AMOUNT
        tenant.customer.save()
        notification_payload = {'amount': TENANT_REFERRER_CASHBACK_AMOUNT}
        Notification(target=tenant.customer, category=CASHBACK_NC, payload=notification_payload).save(
            data={'amount': TENANT_REFERRED_CASHBACK_AMOUNT})
        return True


# noinspection PyUnusedLocal
def get_cash_collection_time_slots(payment):
    now = timezone.now()
    slot_hours = range(10, 19)
    days = [(now + timedelta(days=x)).date() for x in range(7)]
    time_slots = [{"date": day,
                   "time": list(map(lambda x: x.time(),
                                    (filter(lambda x: x > now + timedelta(hours=1),
                                            [timezone.make_aware(datetime.combine(day, time(hour)))
                                             for hour in slot_hours]))))} for day in days]
    if len(time_slots[0]['time']) is 0:
        time_slots.pop(0)
    return time_slots


def get_tenant_profile_completion(tenant):
    """
    Function to get tenant profile completion % and missing fields.
    :param tenant: tenant object
    :return: list of missing fields and completion percentage
    """
    required_fields = {
        'Parent\'s Name': tenant.parent_name,
        'Parent\'s Phone No.': tenant.parent_phone_no,
        'Permanent Address': tenant.permanent_address.complete_address,
        'Date of Birth': tenant.customer.dob
    }

    missing_fields = []

    for field_name, field_value in required_fields.items():
        if field_value in [None, '']:
            missing_fields.append(field_name)

    completion_percentage = round((1 - len(missing_fields) / len(required_fields)) * 100, 2)
    return missing_fields, completion_percentage
