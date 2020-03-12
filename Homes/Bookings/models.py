from datetime import timedelta

from dateutil import relativedelta
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from multiselectfield import MultiSelectField

from Common.models import PaymentCategory
from Common.utils import DEPOSIT, PENDING, CANCELLED, PAID
from Homes.Bookings.tasks import send_booking_invoice_email, send_booking_cancellation_sms, \
    update_affiliate_conversion_details_to_lead_tool
from Homes.Bookings.utils import BookingStatusCategories, BOOKING_PARTIAL, TOKEN_AMOUNT, ONBOARDING_CHARGES, \
    FacilityItemTypeCategories, BOOKING_COMPLETE, BookingFacilityStatusChoices, FACILITY_ALLOCATED, BOOKING_CANCELLED, \
    BOOKING_CANCELLATION_REASON_1, MonthlyRentStatusCategories, NEW_TENANT_BOOKING, BookingTypeCategories, \
    EXISTING_TENANT_BOOKING, change_booked_space_status, reset_booked_space_status, \
    get_tenant_digital_signature_while_move_in_upload_path, AgreementVerificationStatusChoices, \
    AGREEMENT_SIGN_NOT_UPLOADED
from Homes.Houses.models import Space
from Homes.Houses.utils import SOLD_OUT, AVAILABLE, HouseAccomodationAllowedCategories, \
    HouseAccomodationTypeCategories, generate_accomodation_allowed_str
from Homes.Owners.models import OwnerMonthlyEarning
from Homes.Owners.utils import get_owner_month_start_time, get_owner_month_end_time
from Homes.Tenants.models import TenantPayment
from Homes.Tenants.utils import BOOKING_PAYMENT, MOVEIN_PAYMENT, MONTHLY_RENT_PAYMENT, BOOKING_PAYMENT_DESCRIPTION, \
    MOVEIN_PAYMENT_DESCRIPTION, MONTHLY_RENT_PAYMENT_DESCRIPTION
from utility.time_utils import get_date_str


class Booking(models.Model):
    space = models.ForeignKey('Houses.Space', null=True, on_delete=models.SET_NULL, related_name="bookings")
    tenant = models.ForeignKey('Tenants.Tenant', null=True, on_delete=models.SET_NULL, related_name="bookings")
    type = models.CharField(max_length=50, default=NEW_TENANT_BOOKING, choices=BookingTypeCategories)
    status = models.CharField(max_length=200, default=BOOKING_PARTIAL, choices=BookingStatusCategories)
    license_start_date = models.DateTimeField(null=False, blank=False)
    license_end_date = models.DateTimeField(null=True, blank=True)
    lock_in_period = models.IntegerField(blank=True, null=True, default=6)

    rent = models.FloatField(default=0)
    security_deposit = models.FloatField(default=0)
    security_deposit_by_months = models.PositiveIntegerField(default=2)
    token_amount = models.FloatField(default=TOKEN_AMOUNT)
    onboarding_charges = models.FloatField(default=ONBOARDING_CHARGES)
    promo_code = models.ForeignKey('Promotions.PromoCode', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='bookings')

    paid_token_amount = models.BooleanField(default=False)
    paid_movein_charges = models.BooleanField(default=False)

    moved_out = models.BooleanField(default=False)
    move_in_notes = models.TextField(blank=True, null=True)
    move_out_notes = models.TextField(blank=True, null=True)
    area_manager_notes = models.TextField(blank=True, null=True)

    agreement_signed = models.BooleanField(default=False)
    agreement_verification_status = models.CharField(max_length=30, choices=AgreementVerificationStatusChoices,
                                                     default=AGREEMENT_SIGN_NOT_UPLOADED)
    agreement_verification_error_notes = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ('license_start_date',)

    def save(self, *args, **kwargs):
        # set booking rent and security deposit for new tenant booking
        if not self.pk:
            if self.type == NEW_TENANT_BOOKING:
                self.rent = self.space.rent
                self.security_deposit = self.space.security_deposit
                self.security_deposit_by_months = self.space.security_deposit_by_months
            elif self.type == EXISTING_TENANT_BOOKING:
                self.paid_token_amount = True
                self.paid_movein_charges = True
                self.status = BOOKING_COMPLETE
        super(Booking, self).save(*args, **kwargs)

    @property
    def movein_charges(self):
        # onboarding_charges_are_now_default_to_0 because token amount is now 400(200+200)
        return self.onboarding_charges + self.rent + self.security_deposit

    @property
    def hcash(self):
        return self.payments.aggregate(Sum('discount'))['discount__sum']

    @property
    def total_charges(self):
        return self.movein_charges + self.token_amount - self.hcash


class ExistingTenantOnboarding(models.Model):
    booking = models.OneToOneField('Booking', on_delete=models.SET_NULL, null=True, related_name='onboarding')
    rent = models.FloatField(blank=True, null=True)
    security_deposit = models.FloatField(blank=True, null=True)
    original_license_start_date = models.DateTimeField(blank=True, null=True)
    security_deposit_held_by_owner = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)


class FacilityItem(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=15, blank=True, null=True, choices=FacilityItemTypeCategories)

    def __str__(self):
        return self.name


class BookingFacility(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, null=True, related_name='facilities')
    item = models.ForeignKey('FacilityItem', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    quantity_acknowledged = models.IntegerField(default=0)
    remark = models.CharField(max_length=250, blank=True, null=True)
    status = models.CharField(max_length=50, choices=BookingFacilityStatusChoices, default=FACILITY_ALLOCATED)

    class Meta:
        verbose_name_plural = 'Booking Facilities'

    def __str__(self):
        return "{} x {}".format(self.item, self.quantity)


class MonthlyRent(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, related_name='monthly_rents')
    payment = models.OneToOneField('Tenants.TenantPayment', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='monthly_rent')
    owner_monthly_earning = models.ForeignKey('Owners.OwnerMonthlyEarning', on_delete=models.SET_NULL, null=True,
                                              blank=True, related_name='monthly_rents')

    rent = models.FloatField(default=0)

    start_date = models.DateTimeField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    status = models.CharField(max_length=30, default=PENDING, choices=MonthlyRentStatusCategories)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.pk:
            # if monthly rent not provided explicitly, set booking rent as monthly rent
            if int(self.rent) == 0:
                self.rent = self.booking.rent
        super(MonthlyRent, self).save(*args, **kwargs)

    @property
    def fine(self):
        return self.payment.fine

    @property
    def paid_on(self):
        return self.payment.paid_on

    @property
    def due_date(self):
        return self.payment.due_date

    @property
    def start_date_str(self):
        return get_date_str(timezone.localtime(self.start_date))

    @property
    def end_date_str(self):
        return get_date_str(timezone.localtime(self.start_date + relativedelta.relativedelta(months=1)))


class BookingMoveInDigitalSignature(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='signature')
    signature = models.ImageField(upload_to=get_tenant_digital_signature_while_move_in_upload_path)


# noinspection PyUnresolvedReferences
class AdvanceBooking(models.Model):
    tenant = models.ForeignKey('Tenants.Tenant', on_delete=models.SET_NULL, null=True, related_name='advance_bookings')
    expected_rent = models.FloatField(blank=True, null=True)
    expected_movein_date = models.DateField(blank=True, null=True)
    accomodation_for = MultiSelectField(max_length=25, max_choices=3, choices=HouseAccomodationAllowedCategories)
    space_type = models.CharField(max_length=20, choices=HouseAccomodationTypeCategories)
    space_subtype = models.ForeignKey('Houses.SpaceSubType', on_delete=models.SET_NULL, related_name='advance_bookings',
                                      null=True)
    preferred_location = models.CharField(max_length=250, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=True, auto_now=False)

    promo_code = models.ForeignKey('Promotions.PromoCode', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='advance_bookings')

    cancelled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    @property
    def accomodation_for_str(self):
        return generate_accomodation_allowed_str(self.accomodation_for)


# noinspection PyUnusedLocal
@receiver(pre_save, sender=Booking)
def booking_pre_save_hook(sender, instance, **kwargs):
    old_booking = Booking.objects.filter(id=instance.id).first()
    if not old_booking:
        return

    # change space of other partial bookings if token amount paid in current booking
    if old_booking.paid_token_amount is False and instance.paid_token_amount is True:
        space = instance.space
        if space.availability == SOLD_OUT:
            other_bookings = space.bookings.filter(paid_token_amount=False,
                                                   status=BOOKING_PARTIAL).exclude(pk=instance.pk)
            for booking in other_bookings:
                other_space = Space.objects.filter(house=space.house, subtype=space.subtype,
                                                   availability=AVAILABLE).first()
                if other_space:
                    booking.space = other_space
                else:
                    booking.status = BOOKING_CANCELLED
                booking.save()

    # booking completion tasks
    if old_booking.status == BOOKING_PARTIAL and instance.status == BOOKING_COMPLETE:
        send_booking_invoice_email.delay(instance.id)

    # booking cancellation tasks
    if old_booking.status == BOOKING_PARTIAL and instance.status == BOOKING_CANCELLED:
        send_booking_cancellation_sms.delay(instance.id, BOOKING_CANCELLATION_REASON_1)
        instance.monthly_rents.update(status=CANCELLED)
        for payment in instance.payments.all():
            payment.status = CANCELLED
            payment.save()

    # tenant moved out tasks
    if instance.status == BOOKING_COMPLETE and old_booking.moved_out is False and instance.moved_out is True:
        reset_booked_space_status(instance)


# noinspection PyUnusedLocal
@receiver(post_save, sender=Booking)
def booking_post_save_hook(sender, instance, created, **kwargs):
    if created:
        tenant = instance.tenant

        if instance.type == NEW_TENANT_BOOKING:
            # create token payment
            category, _ = PaymentCategory.objects.get_or_create(name=BOOKING_PAYMENT)
            TenantPayment(user=tenant.customer.user, wallet=tenant.wallet, booking=instance,
                          original_amount=TOKEN_AMOUNT, description=BOOKING_PAYMENT_DESCRIPTION,
                          status=PENDING, type=DEPOSIT, category=category,
                          due_date=timezone.now() + timedelta(days=1)).save()

            # create 1st monthly rent (including move-in charges)
            MonthlyRent(booking=instance, start_date=instance.license_start_date).save()

            # send affiliate referral status to lead tool in case affiliate is involved
            try:
                update_affiliate_conversion_details_to_lead_tool.delay(booking_id=instance.id)
            except Exception as E:
                from utility.logging_utils import sentry_debug_logger
                sentry_debug_logger.debug("error occured in updating affiliate conversion details", exc_info=True)

        elif instance.type == EXISTING_TENANT_BOOKING:
            # create token payment
            if int(instance.token_amount) != 0:
                category, _ = PaymentCategory.objects.get_or_create(name=BOOKING_PAYMENT)
                TenantPayment(user=tenant.customer.user, wallet=tenant.wallet, booking=instance,
                              original_amount=instance.token_amount, description=BOOKING_PAYMENT_DESCRIPTION,
                              status=PENDING, type=DEPOSIT, category=category,
                              due_date=instance.license_start_date).save()

            # create 1st monthly rent (including move-in charges)
            if int(instance.movein_charges) != 0:
                MonthlyRent(booking=instance, start_date=instance.license_start_date).save()

            # set space as booked
            change_booked_space_status(instance)


# noinspection PyUnusedLocal
@receiver(pre_save, sender=MonthlyRent)
def monthly_rent_pre_save_hook(sender, instance, update_fields={'owner_monthly_earning'}, **kwargs):
    old_monthly_rent = MonthlyRent.objects.filter(id=instance.id).first()
    if not old_monthly_rent:
        return

    if old_monthly_rent.status == PENDING and instance.status == PAID:
        # create monthly earning object for a new month for the owner (if not exists)
        instance.owner_monthly_earning, _ = OwnerMonthlyEarning.objects.get_or_create(
            owner=instance.booking.space.house.owner, start_date=get_owner_month_start_time(t=instance.paid_on),
            end_date=get_owner_month_end_time(t=instance.paid_on))


# noinspection PyUnusedLocal
@receiver(post_save, sender=MonthlyRent)
def monthly_rent_post_save_hook(sender, instance, created, **kwargs):
    if created:
        instance.payment = TenantPayment.objects.create(user=instance.booking.tenant.customer.user,
                                                        wallet=instance.booking.tenant.wallet, booking=instance.booking,
                                                        due_date=instance.start_date, status=PENDING, type=DEPOSIT)
        if instance.booking.monthly_rents.count() == 1:
            # first monthly rent of a booking includes
            # move-in charges (rent + security deposit + onboarding charges)
            instance.payment.category, _ = PaymentCategory.objects.get_or_create(name=MOVEIN_PAYMENT)
            instance.payment.description = MOVEIN_PAYMENT_DESCRIPTION
            instance.payment.original_amount = instance.booking.movein_charges
        else:
            instance.payment.category, _ = PaymentCategory.objects.get_or_create(name=MONTHLY_RENT_PAYMENT)
            instance.payment.description = MONTHLY_RENT_PAYMENT_DESCRIPTION.format(instance.start_date_str,
                                                                                   instance.end_date_str)
            instance.payment.original_amount = instance.rent
        instance.payment.save()

    if instance.owner_monthly_earning:
        # owner's monthly earning depends on monthly rent
        # hence, after saving monthly rent, save the owner's monthly earnings as well.
        instance.owner_monthly_earning.save()
