from random import randint

from django.db import models
from django.db.models import Min
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from geopy import units, distance
from multiselectfield import MultiSelectField

from Common.models import AddressDetail
from Homes.AreaManagers.tasks import area_manager_house_visit_notify
from Homes.Houses.utils import (HouseTypeCategories, HouseFurnishTypeCategories, HouseAccomodationAllowedCategories,
                                HouseAccomodationTypeCategories, AmenityTypeCategories, get_house_picture_upload_path,
                                get_amenity_picture_upload_path, get_sub_amenity_picture_upload_path, FLAT,
                                SHARED_ROOM, PRIVATE_ROOM, SpaceAvailabilityCategories, AVAILABLE, SOLD_OUT,
                                HousePlanCategories, HouseApplicationStatusCategories,
                                HouseApplicationCurrentStayStatusCategories, NEW_APPLICATION, ExistingFacilityChoices,
                                generate_accomodation_allowed_str, HouseSearchSlugFieldCategories,
                                get_monthly_expense_category_image_upload_path, get_bill_picture_upload_path,
                                get_category_image_upload_path)

from utility.logging_utils import sentry_debug_logger


class MonthlyExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=get_monthly_expense_category_image_upload_path, null=True, blank=True)

    # svg = models.FileField(upload_to=get_amenity_picture_upload_path, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Monthly expense categories'

    def __str__(self):
        return self.name

    def get_expense_category_image_html(self):
        if self.image:
            return mark_safe('<img src="{}" width="80" height="80" />'.format(self.image.url))
        else:
            return None

    get_expense_category_image_html.short_description = 'Expense Category Image'
    get_expense_category_image_html.allow_tags = True


class HouseMonthlyExpense(models.Model):
    house = models.ForeignKey('House', on_delete=models.CASCADE, related_name='monthly_expenses', null=True)
    category = models.ForeignKey('MonthlyExpenseCategory', on_delete=models.CASCADE,
                                 related_name='house_monthly_expenses')
    amount = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Amenity(models.Model):
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=25, blank=True, null=True, choices=AmenityTypeCategories)
    image = models.ImageField(upload_to=get_amenity_picture_upload_path, null=True, blank=True)
    svg = models.FileField(upload_to=get_amenity_picture_upload_path, null=True, blank=True)
    is_major = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Amenities'

    def __str__(self):
        return self.name

    def get_amenity_image_html(self):
        if self.image:
            return mark_safe('<img src="{}" width="80" height="80" />'.format(self.image.url))
        elif self.svg:
            return "<object type='image/svg+xml' data='{}'>Your browser does not support SVG</object>".format(
                self.svg.url)
        else:
            return None

    get_amenity_image_html.short_description = 'Amenity Image'
    get_amenity_image_html.allow_tags = True


class SubAmenity(models.Model):
    name = models.CharField(max_length=50)
    amenity = models.ForeignKey('Amenity', on_delete=models.CASCADE, related_name='sub_amenities')
    image = models.ImageField(upload_to=get_sub_amenity_picture_upload_path, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Sub Amenities'

    def __str__(self):
        return self.name

    def get_sub_amenity_image_html(self):
        if self.image:
            return mark_safe('<img src="{}" width="80" height="80" />'.format(self.image.url))
        else:
            return None

    get_sub_amenity_image_html.short_description = 'SubAmenity Image'
    get_sub_amenity_image_html.allow_tags = True


class HouseAmenity(models.Model):
    house = models.ForeignKey('House', on_delete=models.CASCADE, related_name='amenities')
    amenity = models.ForeignKey('Amenity', on_delete=models.CASCADE, related_name='house_amenities')
    sub_amenities = models.ManyToManyField('SubAmenity', related_name='house_sub_amenities', blank=True)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name_plural = 'House Amenities'

    def __str__(self):
        return str(self.id)


class ExistingFacility(models.Model):
    """
    For house owner's service agreement
    """
    house = models.ForeignKey('House', on_delete=models.CASCADE, related_name='existing_facilities')
    type = models.CharField(max_length=25, choices=ExistingFacilityChoices)
    name = models.CharField(max_length=150)
    count = models.IntegerField(default=1)

    class Meta:
        verbose_name_plural = 'Existing facilities'

    def __str__(self):
        return str(self.name)


class Bed(models.Model):
    room = models.ForeignKey('SharedRoom', on_delete=models.CASCADE, related_name='beds')
    bed_no = models.CharField(max_length=10, blank=True, null=True)

    availability = models.CharField(max_length=20, default=AVAILABLE, choices=SpaceAvailabilityCategories)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.bed_no = str(self.room.beds.count() + 1)
        super(Bed, self).save(*args, **kwargs)


class SharedRoom(models.Model):
    space = models.OneToOneField('Space', on_delete=models.PROTECT, null=True, related_name='shared_room')
    bed_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.id)

    @property
    def free_bed_count(self):
        return self.beds.filter(availability=AVAILABLE, visible=True).count()


class PrivateRoom(models.Model):
    space = models.OneToOneField('Space', on_delete=models.PROTECT, null=True, related_name='private_room')

    def __str__(self):
        return str(self.id)


class Flat(models.Model):
    space = models.OneToOneField('Space', on_delete=models.PROTECT, null=True, related_name='flat')

    def __str__(self):
        return str(self.id)


class SpaceSubType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent_type = models.CharField(max_length=20, choices=HouseAccomodationTypeCategories, blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Space(models.Model):
    house = models.ForeignKey('House', on_delete=models.PROTECT, related_name='spaces')
    name = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=20, choices=HouseAccomodationTypeCategories)
    subtype = models.ForeignKey('SpaceSubType', on_delete=models.SET_NULL, related_name='spaces', null=True)

    rent = models.FloatField(default=0)
    security_deposit = models.FloatField(default=0)
    security_deposit_by_months = models.PositiveIntegerField(default=2)
    commission = models.FloatField(default=0)

    availability = models.CharField(max_length=20, default=AVAILABLE, choices=SpaceAvailabilityCategories)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name) + '({})'.format(self.id)


class HouseManager(models.Manager):
    @staticmethod
    def nearby(latitude, longitude, distance_range=5):
        queryset = House.objects.filter(visible=True)
        rough_distance = units.degrees(arcminutes=units.nautical(kilometers=distance_range)) * 2
        latitude, longitude = float(latitude), float(longitude)
        queryset = queryset.filter(address__latitude__range=(latitude - rough_distance, latitude + rough_distance),
                                   address__longitude__range=(longitude - rough_distance, longitude + rough_distance))
        return queryset

    @staticmethod
    def sorted_nearby(latitude, longitude, distance_range=5, queryset=None):
        if not queryset:
            queryset = HouseManager.nearby(latitude, longitude, distance_range)
        result = []
        for house in queryset:
            exact_distance = distance.distance((latitude, longitude), (house.address.latitude,
                                                                       house.address.longitude)).km
            result.append((house, exact_distance))

        result.sort(key=lambda x: x[1])
        return result


class PopularLocation(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=200, blank=True, null=True)


class House(models.Model):
    owner = models.ForeignKey('Owners.Owner', on_delete=models.PROTECT, related_name='houses')
    application = models.ForeignKey('HouseApplication', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='house')
    agreement_commencement_date = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    rules = models.TextField(null=True, blank=True)
    cover_pic_url = models.CharField(max_length=500, blank=True, null=True)
    preferred_food = models.CharField(max_length=200, blank=True, null=True)
    area_managers = models.ManyToManyField('AreaManagers.AreaManager', related_name='houses')

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)
    available_from = models.DateTimeField(null=True, blank=True)
    available = models.BooleanField(default=True)
    visible = models.BooleanField(default=False)

    bhk_count = models.PositiveIntegerField(default=1)
    house_type = models.CharField(max_length=25, blank=True, null=True, choices=HouseTypeCategories)
    furnish_type = models.CharField(max_length=25, blank=True, null=True, choices=HouseFurnishTypeCategories)
    available_accomodation_types = MultiSelectField(max_length=25, max_choices=3,
                                                    choices=HouseAccomodationTypeCategories)
    accomodation_allowed = MultiSelectField(max_length=25, max_choices=3, choices=HouseAccomodationAllowedCategories)
    house_size = models.CharField(max_length=20, blank=True, null=True)

    two_wheeler_parking_available = models.BooleanField(default=False)
    four_wheeler_parking_available = models.BooleanField(default=False)

    rent_included_expenses = models.ManyToManyField('MonthlyExpenseCategory',
                                                    related_name='rent_included_houses', blank=True)

    managed_by = models.ForeignKey('Owners.Owner', on_delete=models.CASCADE, null=True,
                                   blank=True, related_name="self_managed_houses")

    objects = HouseManager()

    def __str__(self):
        return "{}: {}".format(self.id, self.name)

    @property
    def flats(self):
        return Flat.objects.filter(space__house=self)

    @property
    def private_rooms(self):
        return PrivateRoom.objects.filter(space__house=self)

    @property
    def shared_rooms(self):
        return SharedRoom.objects.filter(space__house=self)

    @property
    def available_flat_count(self):
        return self.flats.filter(space__availability=AVAILABLE).count()

    @property
    def available_room_count(self):
        return self.shared_rooms.filter(space__availability=AVAILABLE).count()

    @property
    def available_bed_count(self):
        return Bed.objects.filter(room__space__house=self, availability=AVAILABLE).count()

    @property
    def rent_from(self):
        return self.spaces.filter(visible=True).aggregate(Min('rent'))['rent__min']

    @property
    def security_deposit_from(self):
        # Deprecated
        # return self.spaces.filter(visible=True).aggregate(Min('security_deposit'))['security_deposit__min']
        try:
            qs = self.spaces.filter(visible=True)
            no_of_months = min(qs, key=lambda x: x.security_deposit_by_months).security_deposit_by_months
            if no_of_months == 1:
                month_suffix = ''
            else:
                month_suffix = 's'

            return str(no_of_months) + " Month" + month_suffix

        except Exception as E:
            return self.spaces.filter(visible=True).aggregate(Min('security_deposit'))['security_deposit__min']

    @property
    def accomodation_allowed_str(self):
        return generate_accomodation_allowed_str(self.accomodation_allowed)

    @property
    def space_types_dict(self):
        spaces = self.spaces.filter(visible=True)
        space_types_metadata = spaces.values_list('type', 'subtype__name').distinct()
        space_types_dict = {x[0]: [y[1] for y in space_types_metadata if y[0] == x[0]] for x in space_types_metadata}
        return space_types_dict

    @property
    def rent_excluded_expenses(self):
        return MonthlyExpenseCategory.objects.exclude(id__in=self.rent_included_expenses.all())

    @property
    def display_title(self):
        try:
            return str(self.bhk_count) + " BHK " + str(self.description) + ' in ' + str(self.address.city)
        except Exception as E:
            sentry_debug_logger.debug(str(E), exc_info=True)
            return str(self.bhk_count) + " BHK " + str(self.description)


class HouseAddressDetail(AddressDetail):
    house = models.OneToOneField('House', on_delete=models.CASCADE, related_name='address')


class HousePicture(models.Model):
    house = models.ForeignKey('House', on_delete=models.DO_NOTHING, related_name='pictures')
    image = models.ImageField(upload_to=get_house_picture_upload_path, null=True, blank=True)
    is_cover_pic = models.BooleanField(default=False)
    rank = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)


class HouseVisit(models.Model):
    house = models.ForeignKey('House', on_delete=models.SET_NULL, null=True, related_name='visits')
    customer = models.ForeignKey('UserBase.Customer', on_delete=models.SET_NULL, null=True, related_name='house_visits')
    area_manager = models.ForeignKey('AreaManagers.AreaManager', on_delete=models.SET_NULL, null=True,
                                     related_name='house_visits')
    code = models.CharField(max_length=10, blank=True, null=True)
    scheduled_visit_time = models.DateTimeField(blank=True, null=True)

    customer_rating = models.IntegerField(default=0)
    customer_feedback = models.TextField(blank=True, null=True)
    area_manager_notes = models.TextField(blank=True, null=True)
    visited = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    actual_visit_time = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        ordering = ('-scheduled_visit_time',)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.id:
            self.code = str(randint(111111, 999999))
        super(HouseVisit, self).save(*args, **kwargs)


class HouseApplication(models.Model):
    owner = models.ForeignKey('Owners.Owner', on_delete=models.SET_NULL, null=True, related_name='applications')
    plan = models.CharField(max_length=100, blank=True, null=True, choices=HousePlanCategories)
    house_type = models.CharField(max_length=25, blank=True, null=True, choices=HouseTypeCategories)
    furnish_type = models.CharField(max_length=25, blank=True, null=True, choices=HouseFurnishTypeCategories)
    accomodation_allowed = MultiSelectField(max_length=25, max_choices=3, choices=HouseAccomodationAllowedCategories)
    current_stay_status = models.CharField(max_length=50, blank=True, null=True,
                                           choices=HouseApplicationCurrentStayStatusCategories)
    bhk_count = models.PositiveIntegerField(default=1, blank=True, null=True)
    current_rent = models.FloatField(blank=True, null=True)
    current_security_deposit = models.FloatField(blank=True, null=True)
    expected_rent = models.FloatField(blank=True, null=True)
    expected_security_deposit = models.FloatField(blank=True, null=True)

    status = models.CharField(max_length=20, default=NEW_APPLICATION, choices=HouseApplicationStatusCategories)

    def __str__(self):
        return str(self.id)


class HouseApplicationAddressDetail(AddressDetail):
    application = models.OneToOneField('HouseApplication', on_delete=models.CASCADE, related_name='address')


class HouseFurnishingBill(models.Model):
    house = models.ForeignKey('House', on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField()
    gst = models.FloatField()
    cleared = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    @property
    def subtotal(self):
        return sum(item.price for item in self.items.all())

    @property
    def total(self):
        return self.subtotal + self.gst


class HouseFurnishingItem(models.Model):
    bill = models.ForeignKey('HouseFurnishingBill', on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=250)
    price = models.FloatField()

    def __str__(self):
        return self.description


class HouseSearchSlug(models.Model):
    slug = models.CharField(max_length=500)
    fields = MultiSelectField(max_length=500, blank=True, max_choices=10, choices=HouseSearchSlugFieldCategories)

    rent_max = models.FloatField(default=0)
    furnish_type = models.CharField(max_length=25, blank=True, null=True, choices=HouseFurnishTypeCategories)
    house_type = models.CharField(max_length=25, blank=True, null=True, choices=HouseTypeCategories)
    accomodation_allowed = MultiSelectField(max_length=25, max_choices=3, blank=True,
                                            choices=HouseAccomodationAllowedCategories)
    bhk_count = models.PositiveIntegerField(default=1)
    shared_room_bed_count = models.PositiveIntegerField(default=2)
    accomodation_type = MultiSelectField(max_length=25, max_choices=3, blank=True,
                                         choices=HouseAccomodationTypeCategories)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    radius = models.FloatField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.slug)


class SampleData(models.Model):
    query_params = models.TextField(null=True, blank=True)
    body_data = models.TextField(null=True, blank=True)


class Occupation(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return str(self.name)


class BillCategory(models.Model):
    name = models.CharField(max_length=30, unique=True)
    image = models.ImageField(upload_to=get_category_image_upload_path, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Bill Categories"

    def __str__(self):
        return self.name


class Bill(models.Model):
    owner = models.ForeignKey('Owners.Owner', on_delete=models.PROTECT)
    house = models.ForeignKey('Houses.House', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.FloatField()
    category = models.ForeignKey(BillCategory, on_delete=models.PROTECT, null=True, blank=True)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    picture = models.ImageField(upload_to=get_bill_picture_upload_path, null=True, blank=True)
    tenant_group = models.ForeignKey('Owners.TenantGroup', on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return str(self.id)


class BillSplit(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name='splits')
    tenant = models.ForeignKey('Tenants.Tenant', on_delete=models.PROTECT, related_name='bills')
    amount = models.FloatField()
    paid = models.BooleanField(default=False)
    due_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        unique_together = ('bill', 'tenant')


# class HouseReview(models.Model):
#     tenant = models.ForeignKey('Tenants.Tenant', on_delete=models.PROTECT)
#     house = models.ForeignKey(House, on_delete=models.PROTECT)
#     content = models.TextField(max_length=250)
#     rating = models.IntegerField()
#
#     created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
#     modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)
#
#     def __str__(self):
#         return "({}) : {}".format(str(self.id), str(self.content)[:10]+"...")


# noinspection PyUnusedLocal
@receiver(post_save, sender=HouseApplication)
def create_house_application_address_object(sender, instance, created, **kwargs):
    if created:
        HouseApplicationAddressDetail(application=instance).save()
        House.objects.create(application=instance, owner=instance.owner)


# noinspection PyUnusedLocal
@receiver(post_save, sender=House)
def create_house_address_object(sender, instance, created, **kwargs):
    if created:
        HouseAddressDetail(house=instance).save()


# noinspection PyUnusedLocal
@receiver(post_save, sender=Space)
def update_house_availability(sender, instance, **kwargs):
    house = instance.house
    house.available = True if house.spaces.filter(visible=True, availability=AVAILABLE).count() else False
    house.save()


# noinspection PyUnusedLocal
@receiver(post_save, sender=SharedRoom)
def update_beds(sender, instance, **kwargs):
    # update bed resources
    beds = instance.beds.all()
    if instance.bed_count > len(beds):
        for _ in range(instance.bed_count - len(beds)):
            Bed.objects.create(room=instance)
    elif instance.bed_count < len(beds):
        extra_beds_count = len(beds) - instance.bed_count
        extra_available_beds = instance.beds.filter(availability=AVAILABLE)
        for extra_bed in extra_available_beds[:extra_beds_count]:
            extra_bed.delete()
        remaining_beds = instance.beds.all()
        if instance.bed_count < len(remaining_beds):
            for bed in remaining_beds[:(len(remaining_beds) - instance.bed_count)]:
                bed.delete()


# noinspection PyUnusedLocal
@receiver(post_save, sender=Bed)
def update_room_availability(sender, instance, **kwargs):
    room = instance.room
    room.space.availability = AVAILABLE if room.beds.filter(availability=AVAILABLE, visible=True).count() else SOLD_OUT
    room.space.save()


# noinspection PyUnusedLocal
def sold_out_all_beds(instance):
    instance.shared_room.beds.update(availability=SOLD_OUT)


@receiver(post_save, sender=Space)
def create_space_type_object(sender, instance, created, **kwargs):
    if instance.type == FLAT:
        Flat.objects.get_or_create(space=instance)
        SharedRoom.objects.filter(space=instance).delete()
        PrivateRoom.objects.filter(space=instance).delete()
    elif instance.type == SHARED_ROOM:
        SharedRoom.objects.get_or_create(space=instance)
        Flat.objects.filter(space=instance).delete()
        PrivateRoom.objects.filter(space=instance).delete()
        if instance.availability == SOLD_OUT:
            sold_out_all_beds(instance)

    elif instance.type == PRIVATE_ROOM:
        PrivateRoom.objects.get_or_create(space=instance)
        SharedRoom.objects.filter(space=instance).delete()
        Flat.objects.filter(space=instance).delete()


# noinspection PyUnusedLocal
@receiver(post_save, sender=HousePicture)
def house_picture_post_save_task(sender, instance, **kwargs):
    house = instance.house
    if instance.is_cover_pic:
        house.cover_pic_url = instance.image.url
        house.save()
        last_cover_pic = house.pictures.filter(is_cover_pic=True).exclude(id=instance.id).first()
        if last_cover_pic:
            last_cover_pic.is_cover_pic = False
            super(HousePicture, last_cover_pic).save()


# noinspection PyUnusedLocal
@receiver(pre_save, sender=HouseVisit)
def house_visit_pre_save_hook(sender, instance, **kwargs):
    old_visit = HouseVisit.objects.filter(id=instance.id).first()
    if not old_visit:
        return

    if not old_visit.cancelled and instance.cancelled:
        from Homes.Houses.tasks import notify_scout_visit_cancelled
        notify_scout_visit_cancelled.delay(instance.id)


# noinspection PyUnusedLocal
@receiver(post_save, sender=HouseVisit)
def house_visit_post_save_task(sender, instance, created, **kwargs):
    if created:
        area_manager_house_visit_notify.delay(instance.id)


@receiver(post_save, sender=BillSplit)
def bill_split_post_save_task(**kwargs):
    instance = kwargs['instance']
    if instance.paid:
        all_bill_splits = instance.bill.splits.all()
        paid_bill_splits = all_bill_splits.filter(paid=True)
        if len(all_bill_splits) == len(paid_bill_splits):
            bill = instance.bill
            bill.paid = True
            bill.save()
