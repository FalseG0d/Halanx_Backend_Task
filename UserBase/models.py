from datetime import date, timedelta

from allauth.socialaccount.models import SocialAccount
from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from geopy import units, distance

from UserBase.utils import (GenderChoices, RelationshipStatusChoices, get_fb_template_upload_path,
                            default_profile_pic_url, default_profile_pic_thumbnail_url, profile_completion_fields,
                            get_picture_upload_path, get_thumbnail_upload_path, generate_customer_referral_code,
                            HALANX_SUPPORT_USERNAME, HALANX_SUPPORT_MESSAGE_ON_CUSTOMER_REGISTER)
from utility.geo_utils import get_region
from utility.image_utils import compress_image
from utility.logging_utils import sentry_debug_logger


class UserInterest(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    sub_interests = models.ManyToManyField("self", blank=True)
    priority = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])

    def __str__(self):
        return str(self.name)


class CustomerManager(models.Manager):
    def nearby(self, latitude, longitude, distance_range=5, ids=None, exclude_ids=None):
        if latitude is None or longitude is None:
            return []
        queryset = self.get_queryset().filter(is_registered=True, is_visible=True)
        if ids is not None:
            queryset = queryset.filter(id__in=ids)
        if exclude_ids is not None:
            queryset = queryset.exclude(id__in=exclude_ids)
        rough_distance = units.degrees(arcminutes=units.nautical(kilometers=distance_range)) * 2
        latitude, longitude = float(latitude), float(longitude)
        queryset = queryset.filter(clatitude__range=(latitude - rough_distance, latitude + rough_distance),
                                   clongitude__range=(longitude - rough_distance, longitude + rough_distance))

        result = []
        for customer in queryset:
            exact_distance = distance.distance((latitude, longitude), (customer.clatitude, customer.clongitude)).m
            result.append((customer, exact_distance))

        result.sort(key=lambda x: x[1])
        return result


class Customer(DirtyFieldsMixin, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    gender = models.CharField(max_length=10, choices=GenderChoices, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_no = models.CharField(max_length=30, unique=True, validators=[RegexValidator('^[+]*\d{10,}$',
                                                                                       message="Phone Number should "
                                                                                               "be contain at least "
                                                                                               "10 numeric numbers")])
    relationship_status = models.CharField(max_length=20, blank=True, null=True, choices=RelationshipStatusChoices)
    profile_completion = models.IntegerField(default=0, blank=True, null=True)
    last_visit = models.DateTimeField(blank=True, null=True)

    address = models.CharField(blank=True, null=True, max_length=300)
    dlatitude = models.FloatField(blank=True, null=True)
    dlongitude = models.FloatField(blank=True, null=True)
    clatitude = models.FloatField(blank=True, null=True)
    clongitude = models.FloatField(blank=True, null=True)
    region = models.ForeignKey('Places.Region', blank=True, null=True, on_delete=models.SET_NULL)

    referrer = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals")
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    hcash = models.FloatField(default=0.0)
    subscription_total = models.FloatField(blank=True, default=0.0)
    account_balance = models.FloatField(blank=True, null=True, default=0.0)

    gcm_id = models.CharField(max_length=500, blank=True, null=True)
    access_token = models.CharField(max_length=300, blank=True, null=True)
    app_version = models.CharField(max_length=50, blank=True, null=True)

    user_interests = models.ManyToManyField("UserInterest", blank=True)
    favorite_items = models.ManyToManyField("Products.Product", blank=True)
    favorite_places = models.ManyToManyField("Places.Place", blank=True)
    follows = models.ManyToManyField("self", related_name='followed_by', symmetrical=False, blank=True)

    is_registered = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)
    receive_notification = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False, blank=True)

    fb_template = models.ImageField(upload_to=get_fb_template_upload_path, null=True, blank=True)
    profile_pic_url = models.CharField(max_length=500, blank=True, null=True, default=default_profile_pic_url)
    profile_pic_thumbnail_url = models.CharField(max_length=500, blank=True, null=True,
                                                 default=default_profile_pic_thumbnail_url)

    campaign = models.ForeignKey('Promotions.Campaign', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='customers')

    objects = CustomerManager()

    def __str__(self):
        return str(self.phone_no)

    @property
    def name(self):
        return self.user.get_full_name()

    @property
    def age(self):
        today = date.today()
        return today.year - self.dob.year if self.dob else 20

    def set_region(self):
        self.region = get_region(self.clatitude, self.clongitude)

    def set_profile_completion(self):
        profile_fields = [
            self.user.first_name,
            self.user.last_name,
            self.user.email,
            self.gender,
            self.bio,
            self.dob,
            self.pictures.filter(is_profile_pic=True).count(),
            self.address,
            self.relationship_status,
            self.is_email_verified,
            Work.objects.filter(customer=self).count(),
            Education.objects.filter(customer=self).count()
        ]
        filled = len(profile_fields) - profile_fields.count(None) - profile_fields.count(0) - profile_fields.count('')
        self.profile_completion = int((filled / len(profile_fields)) * 100)

    def save(self, updated_fields=None, *args, **kwargs):
        if not self.pk:
            # set referral code
            self.referral_code = generate_customer_referral_code(self.user)
        self.hcash = round(max(0.0, self.hcash), 2)
        if self.is_dirty() and set(profile_completion_fields) & set(self.get_dirty_fields().keys()):
            self.set_profile_completion()
        super(Customer, self).save(*args, **kwargs)

    def get_profile_pic_html(self):
        return '<img src="{}" width="80" height="80" />'.format(self.profile_pic_url)

    get_profile_pic_html.short_description = 'Profile Pic'
    get_profile_pic_html.allow_tags = True


class Picture(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='pictures')
    image = models.ImageField(upload_to=get_picture_upload_path, null=True, blank=True)
    thumbnail = models.ImageField(upload_to=get_thumbnail_upload_path, null=True, blank=True)
    is_profile_pic = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.customer.phone_no)

    def save(self, *args, **kwargs):
        if not self.pk:
            temp_name, output, thumbnail = compress_image(self.image, quality=90, create_thumbnail=True)
            self.image.save(temp_name, content=ContentFile(output.getvalue()), save=False)
            self.thumbnail.save(temp_name, content=ContentFile(thumbnail.getvalue()), save=False)

        if self.is_deleted and self.is_profile_pic:
            self.is_profile_pic = False
            self.customer.profile_pic_url = default_profile_pic_url
            self.customer.profile_pic_thumbnail_url = default_profile_pic_thumbnail_url
            self.customer.save()
        super(Picture, self).save(*args, **kwargs)


class Contact(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_no = models.CharField(max_length=30)
    email = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.customer.phone_no)


class Education(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='education')
    school = models.CharField(max_length=50, blank=True, null=True)
    from_year = models.PositiveIntegerField(blank=True, null=True,
                                            validators=[MinValueValidator(1000), MaxValueValidator(9999)])
    to_year = models.PositiveIntegerField(blank=True, null=True,
                                          validators=[MinValueValidator(1000), MaxValueValidator(9999)])
    active = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.school)

    def save(self, *args, **kwargs):
        self.customer.set_profile_completion()
        super(Education, self).save(*args, **kwargs)


class Work(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='work')
    company = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    from_year = models.PositiveIntegerField(blank=True, null=True,
                                            validators=[MinValueValidator(1000), MaxValueValidator(9999)])
    to_year = models.PositiveIntegerField(blank=True, null=True,
                                          validators=[MinValueValidator(1000), MaxValueValidator(9999)])
    active = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.company)

    def save(self, *args, **kwargs):
        self.customer.set_profile_completion()
        super(Work, self).save(*args, **kwargs)


class UserLocation(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='locations')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.customer.name)


class OTP(models.Model):
    phone_no = models.CharField(max_length=30)
    password = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class EmailOTP(models.Model):
    email = models.EmailField(unique=True)
    password = models.IntegerField()
    timestamp = models.DateTimeField(auto_now=True)


class SpamReport(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='spam_reports')
    reporter = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='spams_reported')
    timestamp = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return str(self.customer.name)


# noinspection PyUnusedLocal
@receiver(post_save, sender=UserLocation)
def update_customer_region(sender, instance, *args, **kwargs):
    customer = instance.customer
    latest = timezone.now() - timedelta(hours=3)
    if not customer.locations.filter(timestamp__gte=latest).count():
        customer.set_region()
        customer.save()


# noinspection PyUnusedLocal
@receiver(post_save, sender=Work)
@receiver(post_save, sender=Education)
def update_customer_profile_completion(sender, instance, *args, **kwargs):
    customer = instance.customer
    customer.set_profile_completion()
    customer.save()


# noinspection PyUnusedLocal
@receiver(post_save, sender=Picture)
def customer_picture_post_save_task(sender, instance, *args, **kwargs):
    if instance.is_profile_pic:
        instance.customer.profile_pic_url = instance.image.url
        instance.customer.profile_pic_thumbnail_url = instance.thumbnail.url
        instance.customer.save()
        last_profile_pic = instance.customer.pictures.filter(is_profile_pic=True).exclude(id=instance.id).first()
        if last_profile_pic:
            last_profile_pic.is_profile_pic = False
            super(Picture, last_profile_pic).save()


def create_halanx_support_default_initial_message_for_registering_customer(customer):
    from Chat.models import Conversation
    from Chat.models import Message

    halanx_support_customer = Customer.objects.get(user__username=HALANX_SUPPORT_USERNAME)
    conv = Conversation.objects.filter(participants=halanx_support_customer).filter(participants=customer)
    if not conv:
        conv = Conversation.objects.create()
        conv.participants.add(customer)
        conv.participants.add(halanx_support_customer)
        Message.objects.get_or_create(conversation=conv, sender=halanx_support_customer, receiver=customer,
                                      message=HALANX_SUPPORT_MESSAGE_ON_CUSTOMER_REGISTER)


# noinspection PyUnusedLocal
@receiver(post_save, sender=Customer)
def customer_post_save_task(sender, instance, created, **kwargs):
    if created:
        try:
            if instance.user.username != HALANX_SUPPORT_USERNAME:
                # Creating Conversation and message between new customer and halanx support
                create_halanx_support_default_initial_message_for_registering_customer(customer=instance)
        except Exception as E:
            sentry_debug_logger.error(str(E))

        # create new cart for customer
        from Carts.models import Cart
        Cart.objects.get_or_create(customer=instance)
        # create new tenant object
        from Homes.Tenants.models import Tenant
        Tenant.objects.get_or_create(customer=instance)
        return
        # send welcome mail
        from UserBase.tasks import send_welcome_mail
        send_welcome_mail.delay(instance.user.first_name, instance.user.email)
        # populate news feed
        from News.tasks import add_articles_to_feed
        add_articles_to_feed.delay(instance.id)
        # set customer profile pic from fb
        from UserBase.tasks import set_profile_pic_from_social_account
        if SocialAccount.objects.filter(user=instance.user).count():
            set_profile_pic_from_social_account.delay(instance.id)
