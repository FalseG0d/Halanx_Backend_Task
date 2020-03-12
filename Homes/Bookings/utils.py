from datetime import datetime
from random import randint

from django.template.loader import get_template

from Common.utils import PAID, PENDING, CANCELLED
from Homes.Houses.models import SharedRoom
from Homes.Houses.utils import SHARED_ROOM, SOLD_OUT, AVAILABLE
from utility.file_utils import render_pdf_from_html

# ON-BOARDING Charges are now considered in TOKEN_AMOUNT and ONBOARDING_CHARGES has been removed from move in charges
# or we can say ONBOARDING CHARGES ARE SET to 0

# TOKEN_AMOUNT = 200.0  # Deprecated
# ONBOARDING_CHARGES = 200.0  # Deprecated
from utility.logging_utils import sentry_debug_logger

TOKEN_AMOUNT = 400.0
ONBOARDING_CHARGES = 0

LATE_MONTHLY_RENT_FINE_AMOUNT = 150

NEW_TENANT_BOOKING = 'new_tenant_booking'
EXISTING_TENANT_BOOKING = 'existing_tenant_booking'

BookingTypeCategories = (
    (NEW_TENANT_BOOKING, 'New Tenant Booking'),
    (EXISTING_TENANT_BOOKING, 'Existing Tenant Booking')
)

BOOKING = 'booking'

BOOKING_CANCELLED = 'cancelled'
BOOKING_COMPLETE = 'complete'
BOOKING_PARTIAL = 'partial'

BookingStatusCategories = (
    (BOOKING_CANCELLED, 'Cancelled'),
    (BOOKING_PARTIAL, 'Partially complete'),
    (BOOKING_COMPLETE, 'Complete'),
)

AGREEMENT_SIGN_NOT_UPLOADED = 'unsigned'
AGREEMENT_SIGN_VERIFIED_SUCCESS = 'verified'
AGREEMENT_SIGN_VERIFICATION_ONGOING = 'ongoing'
AGREEMENT_SIGN_VERIFICATION_ERROR = 'error'

AgreementVerificationStatusChoices = (
    (AGREEMENT_SIGN_NOT_UPLOADED, 'Signature not uploaded'),
    (AGREEMENT_SIGN_VERIFIED_SUCCESS, 'Verification Complete'),
    (AGREEMENT_SIGN_VERIFICATION_ONGOING, 'Verification Ongoing'),
    (AGREEMENT_SIGN_VERIFICATION_ERROR, 'Error in Verification'),
)

BOOKING_CANCELLATION_MSG = "Hi {}! Your booking for {} at {} has been cancelled as {}"
BOOKING_CANCELLATION_REASON_1 = "you have not paid the token amount before the due date."
BOOKING_CANCELLATION_REASON_2 = "the space got sold out before your token payment."

SUB_UNIT_ITEM = 'sub_unit'
COMMON_AREA_ITEM = 'common_area'

FacilityItemTypeCategories = (
    (SUB_UNIT_ITEM, 'Sub Unit'),
    (COMMON_AREA_ITEM, 'Common Area')
)

FACILITY_ALLOCATED = 'Allocated'
FACILITY_RETURNED = 'Returned'
FACILITY_LOST = 'Lost'
FACILITY_DAMAGED = 'Damaged'

BookingFacilityStatusChoices = (
    (FACILITY_ALLOCATED, FACILITY_ALLOCATED),
    (FACILITY_RETURNED, FACILITY_RETURNED),
    (FACILITY_LOST, FACILITY_LOST),
    (FACILITY_DAMAGED, FACILITY_DAMAGED),
)

MonthlyRentStatusCategories = (
    (PAID, "Paid"),
    (PENDING, "Pending"),
    (CANCELLED, "Cancelled")
)


def get_tabular_facilities(booking):
    sub_unit_facilities = booking.facilities.filter(item__type=SUB_UNIT_ITEM)
    common_area_facilities = booking.facilities.filter(item__type=COMMON_AREA_ITEM)
    parts = [sub_unit_facilities[::2], sub_unit_facilities[1::2],
             common_area_facilities[::2], common_area_facilities[1::2]]
    max_len = max(map(lambda x: len(x), parts))
    new_parts = []
    for part in parts:
        new_parts.append(part + [''] * (max_len - len(part)))
    return list(zip(*new_parts))


def get_param_dict_for_rent_agreement(booking):
    facilities = get_tabular_facilities(booking)
    param_dict = {'tenant': booking.tenant, 'booking': booking,
                  'owner': booking.space.house.owner, 'facilities': facilities,
                  'agreement_date': booking.license_start_date.date().strftime(
                      '%d %b, %Y'),
                  }
    if booking.agreement_verification_status == AGREEMENT_SIGN_VERIFIED_SUCCESS:
        try:
            param_dict['digital_signature'] = booking.signature.signature.url
        except Exception as E:
            sentry_debug_logger.error(E, exc_info=True)

    return param_dict


def load_rent_agreement(booking):
    param_dict = get_param_dict_for_rent_agreement(booking)
    return render_pdf_from_html("rent_agreement.html", param_dict,
                                '{}_Rent_Agreement.pdf'.format(booking.tenant.customer.name.replace(' ', '_')))


def load_rent_agreement_as_html(booking):
    path = "rent_agreement.html"
    param_dict = get_param_dict_for_rent_agreement(booking)
    template = get_template(path)
    html = template.render(param_dict)
    return html


def change_booked_space_status(booking):
    if booking.space.type != SHARED_ROOM:
        booking.space.availability = SOLD_OUT
        booking.space.save()
    else:
        shared_room = SharedRoom.objects.filter(space=booking.space).first()
        free_bed = shared_room.beds.filter(availability=AVAILABLE, visible=True).first()
        free_bed.availability = SOLD_OUT
        free_bed.save()


def reset_booked_space_status(booking):
    if booking.space.type != SHARED_ROOM:
        booking.space.availability = AVAILABLE
        booking.space.save()
    else:
        shared_room = SharedRoom.objects.filter(space=booking.space).first()
        occupied_bed = shared_room.beds.filter(availability=SOLD_OUT, visible=True).first()
        occupied_bed.availability = AVAILABLE
        occupied_bed.save()


def get_tenant_digital_signature_while_move_in_upload_path(instance, filename):
    return "Bookings/{}/MoveIn/DigitalSignature/{}_{}/".format(instance.booking.id, filename.split('/')[-1],
                                                               randint(111111, 999999))
