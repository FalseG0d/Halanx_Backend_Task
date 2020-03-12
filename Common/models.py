from django.db import models
from django.conf import settings

from Common.utils import DocumentTypeCategories, PENDING, PaymentStatusCategories, PaymentTypeCategories, DEPOSIT, \
    get_payment_category_icon_upload_path


class Document(models.Model):
    type = models.CharField(max_length=30, choices=DocumentTypeCategories)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)


class BankDetail(models.Model):
    account_holder_name = models.CharField(max_length=200, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_type = models.CharField(max_length=10, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    bank_branch = models.CharField(max_length=300, blank=True, null=True)
    bank_branch_address = models.CharField(max_length=300, blank=True, null=True)
    ifsc_code = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)


class AddressDetail(models.Model):
    street_address = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=200, blank=True, null=True)
    zone = models.CharField(max_length=200, blank=True, null=True)
    pincode = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    complete_address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.complete_address

    def save(self, *args, **kwargs):
        self.complete_address = "{}, {}, {}-{}".format(self.street_address, self.city, self.state, self.pincode)
        self.complete_address = self.complete_address.replace('None, ', '').replace('None-', '').replace('-None', '')
        super(AddressDetail, self).save(*args, **kwargs)

    @property
    def coordinates(self):
        return "{},{}".format(self.latitude, self.longitude)


class PaymentCategory(models.Model):
    name = models.CharField(max_length=200)
    icon = models.ImageField(upload_to=get_payment_category_icon_upload_path, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Payment Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.id is None:
            saved_icon = self.icon
            self.icon = None
            super(PaymentCategory, self).save(*args, **kwargs)
            self.icon = saved_icon
            kwargs.pop('force_insert', None)
            super(PaymentCategory, self).save(*args, **kwargs)

    def get_payment_category_icon_html(self):
        if self.icon:
            return '<img src="{}" width="80" height="80" />'.format(self.icon.url)
        else:
            return None

    get_payment_category_icon_html.short_description = 'Icon'
    get_payment_category_icon_html.allow_tags = True


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField(default=0)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, default=PENDING, choices=PaymentStatusCategories)
    type = models.CharField(max_length=30, default=DEPOSIT, choices=PaymentTypeCategories)
    category = models.ForeignKey('Common.PaymentCategory', null=True, on_delete=models.SET_NULL)
    due_date = models.DateTimeField(blank=True, null=True)
    paid_on = models.DateTimeField(blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    last_reminder = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)


class Wallet(models.Model):
    credit = models.FloatField(default=0)
    debit = models.FloatField(default=0)
    balance = models.FloatField(default=0)
    pending_deposit = models.FloatField(default=0)
    pending_withdrawal = models.FloatField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        self.balance = round(self.credit - self.debit, 2)
        super(Wallet, self).save(*args, **kwargs)
