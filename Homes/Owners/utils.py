from random import randint

from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F
from django.utils import timezone

from Common.utils import GST_PERCENTAGE

LEAD_SOURCE_GUEST = 'Guest'
LEAD_SOURCE_AFFILIATE = 'Affiliate'
LEAD_SOURCE_TENANT = 'Tenant'
LEAD_SOURCE_OWNER = 'Owner'


OwnerListingSourceChoices = (
    (LEAD_SOURCE_GUEST, LEAD_SOURCE_GUEST),
    (LEAD_SOURCE_AFFILIATE, LEAD_SOURCE_AFFILIATE),
    (LEAD_SOURCE_TENANT, LEAD_SOURCE_TENANT),
    (LEAD_SOURCE_OWNER, LEAD_SOURCE_OWNER),
)


def get_owner_profile_pic_upload_path(instance, filename):
    return "Owners/{}/{}".format(instance.user.id, filename.split('/')[-1])


def get_owner_team_members_profile_pic_upload_path(instance, filename):
    return "Owners/{}/TeamMembers/{}".format(instance.owner.id, filename.split('/')[-1])


def get_owner_document_upload_path(instance, filename):
    return "Owners/{}/documents/{}/{}_{}".format(instance.owner.user.id, instance.type, randint(111111, 999999),
                                                 filename.split('/')[-1])


def get_owner_document_thumbnail_upload_path(instance, filename):
    return "Owners/{}/documents/{}/thumbnail/{}_{}".format(instance.owner.user.id, instance.type,
                                                           randint(111111, 999999), filename.split('/')[-1])


def get_owner_notification_image_upload_path(instance, filename):
    return "Owners/Notification/{}/{}".format(instance.id, filename.split('/')[-1])


# noinspection PyUnusedLocal
def get_owner_notification_title_and_content(category, data=None):
    title, content = "", ""
    if category == "":
        title = "Sample title"
        content = "Sample content"
    return title, content


OwnerNotificationCategories = (
    ("RentDeposit", "RentDeposit"),
    ("SuccessfulWithdrawal", "SuccessfulWithdrawal"),
)

OwnerCorrespondantRelationCategories = (
    ("S/o", "S/o"),
    ("D/o", "D/o"),
    ("W/o", "W/o")
)

# Owner payment category choices
REFUND_PAYMENT = "Refund"
MONTHLY_EARNING_PAYMENT = "Monthly Earning Payment"
WITHDRAWAL_REQUEST_PAYMENT = "Withdrawal Request Payment"

# Owner payment descriptions
MONTHLY_EARNING_PAYMENT_DESCRIPTION = "Monthly earnings for {} to {}."

# refer and earn cashbacks
OWNER_REFERRER_CASHBACK_AMOUNT = 500


def get_owner_month_start_time(t=timezone.localtime()):
    current_3rd = t.replace(day=3, hour=0, minute=0, second=0, microsecond=0)
    if current_3rd <= t:
        return current_3rd
    else:
        return current_3rd - relativedelta(months=1)


def get_owner_month_end_time(t=timezone.localtime()):
    current_3rd = t.replace(day=3, hour=0, minute=0, second=0, microsecond=0)
    if current_3rd > t:
        return current_3rd
    else:
        return current_3rd + relativedelta(months=1)


def get_rent_detail(monthly_rents):
    if len(monthly_rents):
        total = monthly_rents.aggregate(Sum('rent'))['rent__sum']
        commission = monthly_rents.annotate(commission=F('booking__space__commission') * F('rent') / 100
                                            ).aggregate(Sum('commission'))['commission__sum']
        gst = (GST_PERCENTAGE * commission) / 100
        final = total - commission - gst
    else:
        total, commission, gst, final = 0, 0, 0, 0
    return {'total': total, 'commission': commission, 'gst': gst, 'final': final}
