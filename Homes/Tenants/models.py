from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from Common.models import Document, AddressDetail, BankDetail, Wallet, Payment
from Common.utils import PENDING, PAID, WITHDRAWAL, DEPOSIT, CANCELLED
from Homes.Bookings.utils import BOOKING_PARTIAL, BOOKING_COMPLETE, change_booked_space_status
from Homes.Houses.models import SharedRoom
from Homes.Houses.utils import HouseAccomodationAllowedCategories, \
    HouseAccomodationTypeCategories
from Homes.Tenants.tasks import tenant_referrer_cashback_task, send_tenant_payment_confirmations, \
    add_affiliate_referral_task, notify_scout_new_move_out_task
from Homes.Tenants.utils import get_tenant_document_upload_path, generate_tenant_referral_code, \
    get_tenant_document_thumbnail_upload_path, generate_owner_referral_code, TENANT_PAYMENT_HCASH_LIMIT_PERCENTAGE, \
    BOOKING_PAYMENT, MEAL_TYPES

from UserBase.utils import GenderChoices
from utility.image_utils import compress_image
from utility.logging_utils import sentry_debug_logger


class Tenant(models.Model):
    customer = models.OneToOneField('UserBase.Customer', on_delete=models.PROTECT, related_name='tenant')
    parent_name = models.CharField(max_length=50, null=True, blank=True)
    parent_phone_no = models.CharField(max_length=15, null=True, blank=True)
    has_vehicle = models.BooleanField(default=False)
    favorite_houses = models.ManyToManyField('Houses.House', blank=True)
    tenant_referral_code = models.CharField(max_length=40, blank=True, null=True)
    owner_referral_code = models.CharField(max_length=40, blank=True, null=True)
    referrer = models.ForeignKey('self', blank=True, null=True, related_name='tenant_referrals',
                                 on_delete=models.SET_NULL)
    affiliate_code = models.CharField(max_length=255, blank=True, null=True)

    # emergency contact
    emergency_contact_name = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_email = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_phone_no = models.CharField(max_length=50, null=True, blank=True)

    # company detail
    job_position = models.CharField(max_length=50, null=True, blank=True)
    company_name = models.CharField(max_length=400, null=True, blank=True)
    company_email = models.CharField(max_length=200, blank=True, null=True)
    company_phone_no = models.CharField(max_length=50, null=True, blank=True)
    company_joining_date = models.DateTimeField(blank=True, null=True)
    company_leaving_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "{}: {}".format(self.id, self.customer.name)

    @property
    def name(self):
        return self.customer.name

    @property
    def phone_no(self):
        return self.customer.phone_no

    @property
    def current_booking(self):
        return self.bookings.select_related('space',
                                            'space__house',
                                            'space__house__address').filter(status=BOOKING_COMPLETE,
                                                                            moved_out=False).first()

    @property
    def current_stay(self):
        curr_booking = self.current_booking
        if curr_booking is not None:
            house = curr_booking.space.house
            return "Currently staying at {}, {}, {}.".format(house.name, house.address.street_address,
                                                             house.address.city)
        else:
            return "Not staying at any halanx home currently."


class TenantDocument(Document):
    tenant = models.ForeignKey('Tenant', null=True, on_delete=models.SET_NULL, related_name='documents')
    image = models.ImageField(upload_to=get_tenant_document_upload_path, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=get_tenant_document_thumbnail_upload_path, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.id is None:
            temp_name, output, thumbnail = compress_image(self.image, quality=90, create_thumbnail=True)
            self.image.save(temp_name, content=ContentFile(output.getvalue()), save=False)
            self.thumbnail.save(temp_name, content=ContentFile(thumbnail.getvalue()), save=False)
        super(TenantDocument, self).save(*args, **kwargs)


class TenantPermanentAddressDetail(AddressDetail):
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, related_name='permanent_address')


class TenantCompanyAddressDetail(AddressDetail):
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, related_name='company_address')


class TenantBankDetail(BankDetail):
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, related_name='bank_detail')


class TenantWallet(Wallet):
    tenant = models.OneToOneField('Tenant', on_delete=models.PROTECT, related_name='wallet')

    def __str__(self):
        return str(self.tenant.id)


class TenantPayment(Payment):
    wallet = models.ForeignKey('TenantWallet', null=True, on_delete=models.SET_NULL, related_name='payments')
    transaction = models.ForeignKey('Transaction.CustomerTransaction', blank=True, null=True, on_delete=models.SET_NULL,
                                    related_name='tenant_payments')
    booking = models.ForeignKey('Bookings.Booking', null=True, on_delete=models.SET_NULL, related_name='payments')
    apply_cashback = models.BooleanField(default=False)
    original_amount = models.FloatField(default=0)
    fine = models.FloatField(default=0)
    discount = models.FloatField(default=0)

    @property
    def available_hcash(self):

        if self.category.name == BOOKING_PAYMENT:  # We can't apply cashback on TOKEN_AMOUNT
            return 0

        return round(min(TENANT_PAYMENT_HCASH_LIMIT_PERCENTAGE * (self.wallet.tenant.customer.hcash + self.discount),
                         self.original_amount), 2)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.amount = self.original_amount + self.fine - self.discount
        super(TenantPayment, self).save(*args, **kwargs)


class TenantRequirement(models.Model):
    tenant = models.ForeignKey('Tenant', blank=True, null=True, on_delete=models.SET_NULL,
                               related_name='requirements')
    affiliate_code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    phone_no = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True, choices=GenderChoices)

    preferred_location = models.TextField(blank=True, null=True)
    expected_rent = models.IntegerField(blank=True, null=True)
    expected_movein_date = models.DateTimeField(blank=True, null=True)
    accomodation_for = models.CharField(max_length=50, blank=True, null=True,
                                        choices=HouseAccomodationAllowedCategories)
    accomodation_type = models.CharField(max_length=50, blank=True, null=True, choices=HouseAccomodationTypeCategories)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


# class TenantMoveInRequest(models.Model):
#     tenant = models.ForeignKey(Tenant, null=True, on_delete=models.SET_NULL, related_name='movein_requests')
#     timing = models.DateTimeField()
#
#     created_at = models.DateTimeField(auto_now_add=True)


class TenantMoveOutRequest(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, on_delete=models.SET_NULL, related_name='moveout_requests')
    timing = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)


class TenantLateCheckin(models.Model):
    current_booking = models.ForeignKey('Bookings.Booking', on_delete=models.CASCADE)
    expected_checkin = models.DateTimeField()


class TenantMeal(models.Model):
    date = models.DateField()
    type = models.CharField(max_length=20, choices=MEAL_TYPES)
    accepted_by = models.ManyToManyField(Tenant, blank=True)
    meal = models.CharField(max_length=100)
    house = models.ForeignKey("Houses.House", on_delete=models.CASCADE, related_name="meals")

    @property
    def having(self):
        """
        :return: no of tenants ready for the meal
        """
        return self.accepted_by.count()


# noinspection PyUnusedLocal
@receiver(post_save, sender=TenantPayment)
def tenant_payment_post_save_hook(sender, instance, **kwargs):
    # update tenant wallet
    wallet = instance.wallet
    wallet.debit = sum(payment.amount for payment in wallet.payments.filter(type=WITHDRAWAL, status=PAID))
    wallet.credit = sum(payment.amount for payment in wallet.payments.filter(type=DEPOSIT, status=PAID))
    wallet.pending_deposit = sum(payment.amount for payment in wallet.payments.filter(type=DEPOSIT, status=PENDING))
    wallet.pending_withdrawal = sum(
        payment.amount for payment in wallet.payments.filter(type=WITHDRAWAL, status=PENDING))
    wallet.save()

    # set total transaction amount
    if instance.status == PENDING and instance.transaction:
        instance.transaction.amount = instance.transaction.tenant_payments.aggregate(Sum('amount'))['amount__sum']
        instance.transaction.save()

    # update monthly rent status
    if hasattr(instance, 'monthly_rent') and instance.monthly_rent:
        instance.monthly_rent.status = instance.status
        instance.monthly_rent.save()


# noinspection PyUnusedLocal
@receiver(pre_save, sender=TenantPayment)
def tenant_payment_pre_save_hook(sender, instance, update_fields={'discount', 'amount', 'fine', 'apply_cashback'},
                                 **kwargs):
    # check if an older version of the payment exists or not
    old_payment = TenantPayment.objects.filter(id=instance.id).first()
    if not old_payment:
        return

    payment_cancelled_condition = (old_payment.status != CANCELLED and instance.status == CANCELLED)

    apply_cashback_condition = (instance.status == PENDING and old_payment.apply_cashback is False and
                                instance.apply_cashback is True)
    revoke_cashback_condition = (instance.status == PENDING and old_payment.apply_cashback is True and
                                 instance.apply_cashback is False) or payment_cancelled_condition

    subtract_hcash_condition = (old_payment.status == PENDING and instance.status == PAID and instance.apply_cashback)

    # apply cashback
    if apply_cashback_condition:
        instance.discount = instance.available_hcash
        # Don't subtract hcash from wallet if transaction is incomplete
        # instance.wallet.tenant.customer.hcash -= instance.discount
        # instance.wallet.tenant.customer.save()

    # revoke cashback
    if revoke_cashback_condition:
        # Don't add hcash to wallet if transaction is incomplete
        # instance.wallet.tenant.customer.hcash += instance.discount
        # instance.wallet.tenant.customer.save()
        instance.discount = 0

    # subtract hcash when payment complete
    if subtract_hcash_condition:
        instance.wallet.tenant.customer.hcash -= instance.discount
        instance.wallet.tenant.customer.hcash.save()

    # final payment amount
    instance.amount = instance.original_amount + instance.fine - instance.discount

    # set transaction as cancelled if payment got cancelled
    if payment_cancelled_condition:
        instance.apply_cashback = False
        if instance.transaction:
            instance.transaction.amount = instance.amount
            instance.transaction.cancelled = True
            instance.transaction.save()

    # set previous transaction as cancelled
    if old_payment.transaction and old_payment.transaction != instance.transaction:
        old_payment.transaction.cancelled = True
        old_payment.transaction.save()

    payment_complete_condition = old_payment.status == PENDING and instance.status == PAID

    # tenant payment completion tasks
    if payment_complete_condition:
        if instance.transaction:
            send_tenant_payment_confirmations.delay(instance.id, payment_gateway=instance.transaction.payment_gateway)

        tenant_referrer_cashback_task.delay(instance.wallet.id)

    # booking status update for partial bookings
    booking = instance.booking
    if payment_complete_condition and booking.status == BOOKING_PARTIAL:
        if instance.category.name == BOOKING_PAYMENT:
            booking.paid_token_amount = True
            change_booked_space_status(booking)
        else:
            booking.paid_movein_charges = True
        if booking.paid_token_amount and booking.paid_movein_charges:
            booking.status = BOOKING_COMPLETE
        booking.save()


# noinspection PyUnusedLocal
@receiver(post_save, sender=Tenant)
def create_tenant_detail_objects(sender, instance, created, **kwargs):
    if created:
        TenantWallet(tenant=instance).save()
        TenantPermanentAddressDetail(tenant=instance).save()
        TenantBankDetail(tenant=instance).save()
        TenantCompanyAddressDetail(tenant=instance).save()
        instance.tenant_referral_code = generate_tenant_referral_code(instance)
        instance.owner_referral_code = generate_owner_referral_code(instance)
        super(Tenant, instance).save()


# noinspection PyUnusedLocal
@receiver(post_save, sender=TenantRequirement)
def tenant_requirements_post_save_hook(sender, instance, created, **kwargs):
    if created:
        sentry_debug_logger.debug('created tenant requirement', exc_info=True)
        add_affiliate_referral_task.delay(instance.id)


@receiver(post_save, sender=TenantMoveOutRequest)
def tenant_move_out_request_post_save_hook(sender, instance, created, **kwargs):
    if created:
        notify_scout_new_move_out_task.delay(instance.id)
