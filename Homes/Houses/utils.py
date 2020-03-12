from datetime import timedelta, datetime, time

from django.utils import timezone

WEBSITE_BASE_URL = 'https://halanx.com'

APARTMENT = 'apartment'
INDEPENDENT = 'independent'
VILLA = 'villa'

HouseTypeCategories = (
    (APARTMENT, 'Apartment'),
    (INDEPENDENT, 'Independent House'),
    (VILLA, 'Villa'),
)

FULLY_FURNISHED = 'full'
SEMI_FURNISHED = 'semi'
UNFURNISHED = 'nil'

HouseFurnishTypeCategories = (
    (FULLY_FURNISHED, 'Fully furnished'),
    (SEMI_FURNISHED, 'Semi furnished'),
    (UNFURNISHED, 'Unfurnished')
)

GIRLS = 'girls'
BOYS = 'boys'
FAMILY = 'family'

HouseAccomodationAllowedCategories = (
    (GIRLS, 'Girls'),
    (BOYS, 'Boys'),
    (FAMILY, 'Family')
)

FLAT = 'flat'
PRIVATE_ROOM = 'private'
SHARED_ROOM = 'shared'

HouseAccomodationTypeCategories = (
    (SHARED_ROOM, 'Shared rooms'),
    (PRIVATE_ROOM, 'Private rooms'),
    (FLAT, 'Entire house'),
)

HALANX_MANAGER = "halanx",
SELF_MANAGER = "self"

HouseManagedByCategories = (
    (HALANX_MANAGER, "Halanx Manager"),
    (SELF_MANAGER, "Self Manager"),
)

INHOUSE_AMENITY = "inhouse"
SOCIETY_AMENITY = "society"

AmenityTypeCategories = (
    (INHOUSE_AMENITY, 'In-House'),
    (SOCIETY_AMENITY, 'Society')
)

SOLD_OUT = "Sold Out"
NOT_AVAILABLE = "Not Available"
AVAILABLE = "available"

SpaceAvailabilityCategories = (
    (SOLD_OUT, "Sold Out"),
    (NOT_AVAILABLE, "Not Available"),
    (AVAILABLE, "Available")
)

HousePlanCategories = (
    ("Plan A", "Plan A"),
    ("Plan B", "Plan B"),
    ("Plan C", "Plan C"),
)

HouseApplicationCurrentStayStatusCategories = (
    ("I'm staying", "I'm staying"),
    ("Tenant is staying", "Tenant is staying"),
    ("It's vacant", "It's vacant"),
)

NEW_APPLICATION = "New"
IN_PROGRESS = "In progress"
COMPLETED = "Complete"

HouseApplicationStatusCategories = (
    (NEW_APPLICATION, NEW_APPLICATION),
    (IN_PROGRESS, IN_PROGRESS),
    (COMPLETED, COMPLETED),
)

ExistingFacilityChoices = (
    ("Bedroom", "Bedroom"),
    ("Living Room", "Living Room"),
    ("Kitchen & Dining Hall", "Kitchen & Dining Hall"),
    ("Bathroom", "Bathroom"),
    ("Others", "Others")
)


house_search_slug_fields = ("rent_max", "furnish_type", "house_type", "accomodation_allowed",
                            "bhk_count", "shared_room_bed_count", "accomodation_type", "latitude", "longitude",
                            "radius")

HouseSearchSlugFieldCategories = [[field] * 2 for field in house_search_slug_fields]

# House Bill distribution types
DISTRIBUTION_TYPE_AMOUNT = 'amount'
DISTRIBUTION_TYPE_RATIO = 'ratio'

default_profile_pic_url = "https://d28fujbigzf56k.cloudfront.net/static/img/nopic.jpg"

HOUSE_QUERY_DISTANCE_RANGE = 8

# house visit constants
PENDING_HOUSE_VISIT_MSG = "Hi {}! You have a pending house visit for {} today at {}. " \
                          "You can call our Area Manager {} at {} for any queries.\nThank You."
RESCHEDULE_HOUSE_VISIT_MSG = "Hi {}! You missed your pending house visit for {} today at {}. " \
                             "You can reschedule your house visit as per your convenience through the Halanx App." \
                             "\nThank You."
CANCEL_HOUSE_VISIT_MSG = "Hi {}! Your house visit for {} has been cancelled as you have missed the deadline for " \
                         "the visit. You can create a new house visit as per your convenience through the Halanx App." \
                         "\nThank You."
HOUSE_VISIT_RESCHEDULE_DAYS_LIMIT = 2


def get_house_picture_upload_path(instance, filename):
    return "House/{}/{}/{}".format(instance.house.id, instance.house.pictures.count(), filename.split('/')[-1])


def get_amenity_picture_upload_path(instance, filename):
    return "Amenity/{}.{}".format(instance.name, filename.split('.')[-1])


def get_monthly_expense_category_image_upload_path(instance, filename):
    return "ExpenseCategories/{}.{}".format(instance.name, filename.split('.')[-1])


def get_sub_amenity_picture_upload_path(instance, filename):
    return "SubAmenity/{}.{}".format(instance.name, filename.split('.')[-1])


def get_vendor_profile_pic_upload_path(instance, filename):
    return "Houses/Owners/{}/Vendors/{}".format(instance.owner.id, filename.split('/')[-1])


def get_bill_picture_upload_path(instance, filename):
    return "Houses/Owners/{}/Bills/{}".format(instance.owner.id, filename.split('/')[-1])


def get_category_image_upload_path(instance, filename):
    return "Houses/Bill/Categories/{}/{}".format(instance.name, filename.split('/')[-1])


# noinspection PyUnusedLocal
def get_house_visit_time_slots(house):
    now = timezone.now()
    slot_hours = []
    for i in range(9, 20):
        for j in range(0, 60, 30):
            slot_hours.append((i, j))

    days = [(now + timedelta(days=x)).date() for x in range(7)]
    time_slots = [{"date": day,
                   "time": list(map(lambda x: x.time(),
                                    (filter(lambda x: x > now + timedelta(hours=1),
                                            [timezone.make_aware(datetime.combine(day, time(hour, minute)))
                                             for hour, minute in slot_hours]))))} for day in days]

    if len(time_slots[0]['time']) is 0:
        time_slots.pop(0)

    return time_slots


def generate_accomodation_allowed_str(accomodation_allowed):
    if len(accomodation_allowed) == 3:
        return "All"
    elif len(accomodation_allowed) == 2:
        return "{} and {}".format(*map(lambda x: x.capitalize(), accomodation_allowed))
    elif len(accomodation_allowed) == 1:
        return accomodation_allowed[0].capitalize()


def get_house_url_from_house_id(house_id):
    return WEBSITE_BASE_URL + '/house/' + str(house_id)


HOUSE_VISIT_CANCELLED = 'House Visit Cancelled'
HOUSE_VISIT = 'House Visit'

SCOUT_BACKEND_URL = "https://scout-api.halanx.com"
SCOUT_TASK_URL = SCOUT_BACKEND_URL + "/scouts/task/create/"
