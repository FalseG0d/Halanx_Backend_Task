from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from jsonfield import JSONField

from Common.models import AddressDetail, BankDetail, Document, Wallet, Payment, PaymentCategory
from Common.utils import PENDING, WITHDRAWAL, PAID, DEPOSIT, get_halanx_user
from Homes.Houses.models import House, Occupation
from Homes.Houses.utils import HouseFurnishTypeCategories, get_vendor_profile_pic_upload_path
from Homes.Owners.tasks import add_affiliate_referral_task_owner_listing
from Homes.Owners.tasks import send_monthly_earning_invoice_email, send_owner_payment_confirmation_email
from Homes.Owners.utils import OwnerListingSourceChoices
from Homes.Owners.utils import get_owner_profile_pic_upload_path, get_owner_document_upload_path, \
    get_owner_notification_image_upload_path, get_owner_notification_title_and_content, OwnerNotificationCategories, \
    get_owner_document_thumbnail_upload_path, OwnerCorrespondantRelationCategories, get_rent_detail, \
    MONTHLY_EARNING_PAYMENT, MONTHLY_EARNING_PAYMENT_DESCRIPTION, WITHDRAWAL_REQUEST_PAYMENT, \
    get_owner_team_members_profile_pic_upload_path
from UserBase.utils import GenderChoices
from utility.image_utils import compress_image
from utility.logging_utils import sentry_debug_logger
from utility.time_utils import get_date_str

User = get_user_model()


# noinspection PyUnresolvedReferences
class Owner(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='house_owner')
    phone_no = models.CharField(max_length=30, unique=True, validators=[RegexValidator('^[+]*\d{10,}$',
                                                                                       message="Phone Number should "
                                                                                               "be contain at least "
                                                                                               "10 numeric numbers")])
    dob = models.DateField(null=True, blank=True)
    gstin = models.CharField(max_length=100, blank=True, null=True)

    correspondant_name = models.CharField(max_length=50, null=True, blank=True)
    correspondant_relation = models.CharField(max_length=10, blank=True, null=True,
                                              choices=OwnerCorrespondantRelationCategories)
    correspondant_phone_no = models.CharField(max_length=15, null=True, blank=True)
    profile_pic = models.ImageField(upload_to=get_owner_profile_pic_upload_path, null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    referrer = models.ForeignKey('Tenants.Tenant', blank=True, null=True, on_delete=models.SET_NULL,
                                 related_name='owner_referrals')

    def __str__(self):
        return "{}: {}".format(self.id, self.name)

    @property
    def name(self):
        return self.user.get_full_name()


class OwnerDocument(Document):
    owner = models.ForeignKey('Owner', null=True, on_delete=models.SET_NULL, related_name='documents')
    image = models.ImageField(upload_to=get_owner_document_upload_path, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=get_owner_document_thumbnail_upload_path, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.id is None:
            temp_name, output, thumbnail = compress_image(self.image, quality=90, create_thumbnail=True)
            self.image.save(temp_name, content=ContentFile(output.getvalue()), save=False)
            self.thumbnail.save(temp_name, content=ContentFile(thumbnail.getvalue()), save=False)
        super(OwnerDocument, self).save(*args, **kwargs)


class OwnerAddressDetail(AddressDetail):
    owner = models.OneToOneField('Owner', on_delete=models.CASCADE, related_name='address')


class OwnerBankDetail(BankDetail):
    owner = models.OneToOneField('Owner', on_delete=models.CASCADE, related_name='bank_detail')


class OwnerWallet(Wallet):
    owner = models.OneToOneField('Owner', on_delete=models.PROTECT, related_name='wallet')

    def __str__(self):
        return "{}: {}".format(self.owner.id, self.owner.name)


class OwnerPayment(Payment):
    wallet = models.ForeignKey('OwnerWallet', on_delete=models.SET_NULL, null=True, related_name='payments')
    transaction = models.ForeignKey('Transaction.HouseOwnerTransaction', blank=True, null=True,
                                    on_delete=models.SET_NULL, related_name='owner_payments')


class WithdrawalRequest(models.Model):
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True, related_name='withdrawal_requests')
    payment = models.OneToOneField('OwnerPayment', on_delete=models.SET_NULL, null=True,
                                   related_name='withdrawal_request')
    amount = models.FloatField(default=0)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.payment = OwnerPayment.objects.create(user=self.owner.user, wallet=self.owner.wallet,
                                                       amount=self.amount, description=self.description,
                                                       type=WITHDRAWAL)
            self.payment.category, _ = PaymentCategory.objects.get_or_create(name=WITHDRAWAL_REQUEST_PAYMENT)
            self.payment.save()
        return super(WithdrawalRequest, self).save(*args, **kwargs)

    @property
    def status(self):
        return self.payment.status


class OwnerMonthlyEarning(models.Model):
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True, related_name='monthly_earnings')
    payment = models.OneToOneField('OwnerPayment', on_delete=models.SET_NULL, null=True, related_name='monthly_earning')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    rent = models.FloatField(default=0)
    commission = models.FloatField(default=0)
    gst = models.FloatField(default=0)
    total = models.FloatField(default=0)

    credited = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        rent_detail = get_rent_detail(self.monthly_rents.filter(status=PAID))
        self.rent = rent_detail['total']
        self.commission = rent_detail['commission']
        self.gst = rent_detail['gst']
        self.total = rent_detail['final']
        super(OwnerMonthlyEarning, self).save(*args, **kwargs)

    @property
    def start_date_str(self):
        return get_date_str(self.start_date)

    @property
    def end_date_str(self):
        return get_date_str(self.end_date)


class OwnerNotification(models.Model):
    owner = models.ForeignKey('Owner', on_delete=models.CASCADE, related_name='notifications')
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    category = models.CharField(max_length=50, blank=True, null=True, choices=OwnerNotificationCategories)
    title = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(max_length=200, blank=True, null=True)
    payload = JSONField(blank=True, null=True)
    display = models.BooleanField(default=True)

    def __str__(self):
        return str(self.owner.name)

    def save(self, data=None, *args, **kwargs):
        if not self.pk and self.category:
            self.title, self.content = get_owner_notification_title_and_content(self.category, data=data)
        super(OwnerNotification, self).save(*args, **kwargs)


class OwnerNotificationImage(models.Model):
    image = models.ImageField(upload_to=get_owner_notification_image_upload_path, null=True, blank=True)
    category = models.CharField(max_length=50, blank=True, null=True, choices=OwnerNotificationCategories)

    def __str__(self):
        return str(self.category)

    def get_notification_image_html(self):
        if self.image:
            return '<img src="{}" width="80" height="80" />'.format(self.image.url)
        else:
            return None

    get_notification_image_html.short_description = 'Notification Image'
    get_notification_image_html.allow_tags = True


# This will be added to lead and affiliate tool as well
class OwnerListing(models.Model):
    owner = models.ForeignKey(Owner, null=True, blank=True)

    name = models.CharField(max_length=255, blank=True, null=True)
    phone_no = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True, choices=GenderChoices)
    expected_rent = models.IntegerField(blank=True, null=True)
    bhk_count = models.IntegerField(blank=True, null=True)
    furnish_type = models.CharField(max_length=100, null=True, blank=True, choices=HouseFurnishTypeCategories)
    house_address = models.CharField(max_length=200, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Lead Details
    source_category = models.CharField(max_length=100, choices=OwnerListingSourceChoices, null=True, blank=True)
    source_category_name = models.CharField(max_length=100, null=True, blank=True)

    # Depending on the source category different referrers
    referrer_tenant = models.ForeignKey('Tenants.Tenant', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='owner_listings')
    referrer_owner = models.ForeignKey('Owners.Owner', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='owner_listings')

    affiliate_code = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class TeamMember(models.Model):
    # This model is for team members of an owner for FreeOwnerApp
    name = models.CharField(max_length=100)
    phone_no = models.CharField(max_length=15)
    about = models.TextField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    profile_pic = models.ImageField(upload_to=get_owner_team_members_profile_pic_upload_path, null=True, blank=True)

    owner = models.ForeignKey(Owner, on_delete=models.PROTECT)
    houses = models.ManyToManyField(House, blank=True, related_name='team_members')


# noinspection PyUnusedLocal
@receiver(post_save, sender=Owner)
def owner_post_save_hook(sender, instance, created, **kwargs):
    if created:
        OwnerWallet(owner=instance).save()
        OwnerAddressDetail(owner=instance).save()
        OwnerBankDetail(owner=instance).save()


# noinspection PyUnusedLocal
@receiver(pre_save, sender=OwnerMonthlyEarning)
def owner_monthly_earning_pre_save_hook(sender, instance, **kwargs):
    old_monthly_earning = OwnerMonthlyEarning.objects.filter(id=instance.id).first()
    if not old_monthly_earning:
        return

    if old_monthly_earning.credited is False and instance.credited is True:
        send_monthly_earning_invoice_email.delay(instance.id)


# noinspection PyUnusedLocal
@receiver(post_save, sender=OwnerMonthlyEarning)
def owner_monthly_earning_post_save_hook(sender, instance, created, **kwargs):
    if created:
        instance.payment = OwnerPayment.objects.create(user=get_halanx_user(), wallet=instance.owner.wallet)
        instance.payment.category, _ = PaymentCategory.objects.get_or_create(name=MONTHLY_EARNING_PAYMENT)
        instance.payment.description = MONTHLY_EARNING_PAYMENT_DESCRIPTION.format(instance.start_date_str,
                                                                                  instance.end_date_str)
    instance.payment.amount = instance.total
    instance.payment.save()


# noinspection PyUnusedLocal
@receiver(pre_save, sender=OwnerPayment)
def owner_payment_pre_save_hook(sender, instance, **kwargs):
    old_payment = OwnerPayment.objects.filter(id=instance.id).first()
    if not old_payment:
        return

    if old_payment.status == PENDING and instance.status == PAID:
        send_owner_payment_confirmation_email.delay(instance.id)
        if hasattr(instance, 'monthly_earning') and instance.monthly_earning:
            OwnerMonthlyEarning.objects.filter(payment=instance).update(credited=True)


# noinspection PyUnusedLocal
@receiver(post_save, sender=OwnerPayment)
def owner_payment_post_save_hook(sender, instance, created, **kwargs):
    # update owner wallet
    wallet = instance.wallet
    wallet.debit = sum(payment.amount for payment in wallet.payments.filter(type=WITHDRAWAL, status=PAID))
    wallet.credit = sum(payment.amount for payment in wallet.payments.filter(type=DEPOSIT, status=PAID))
    wallet.pending_deposit = sum(payment.amount for payment in wallet.payments.filter(type=DEPOSIT, status=PENDING))
    wallet.pending_withdrawal = sum(payment.amount for payment in wallet.payments.filter(type=WITHDRAWAL,
                                                                                         status=PENDING))
    wallet.save()


@receiver(post_save, sender=OwnerListing)
def owner_listing_post_save_hook(sender, instance, created, **kwargs):
    if created:
        sentry_debug_logger.debug('created owner listing', exc_info=True)
        add_affiliate_referral_task_owner_listing.delay(instance.id)


class Vendor(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey('Owners.Owner', on_delete=models.PROTECT)
    houses = models.ManyToManyField(House, related_name='vendors', blank=True)
    phone_no = models.CharField(max_length=15)
    occupation = models.ForeignKey(Occupation, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to=get_vendor_profile_pic_upload_path, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class TenantGroup(models.Model):
    tenants = models.ManyToManyField('Tenants.Tenant', blank=False)
    owner = models.ForeignKey('Owners.Owner', on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return str(self.id)