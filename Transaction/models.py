from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from Common.utils import PAID, PlatformChoices
from Transaction.utils import get_deposit_reference_image_upload_path
from utility.online_transaction_utils import PaymentGatewayChoices


class Transaction(models.Model):
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_gateway = models.CharField(max_length=20, null=True, blank=True, choices=PaymentGatewayChoices)
    platform = models.CharField(max_length=20, null=True, blank=True, choices=PlatformChoices)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()

    collector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    collection_time_start = models.DateTimeField(blank=True, null=True)
    collection_time_end = models.DateTimeField(blank=True, null=True)
    actual_collection_time = models.DateTimeField(blank=True, null=True)
    deposited = models.BooleanField(default=False)
    deposit_time = models.DateTimeField(blank=True, null=True)
    deposit_reference = models.TextField(blank=True, null=True)
    deposit_reference_image = models.ImageField(upload_to=get_deposit_reference_image_upload_path,
                                                null=True, blank=True)

    complete = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)


class CustomerTransaction(Transaction):
    customer = models.ForeignKey('UserBase.Customer', null=True, on_delete=models.SET_NULL)


class StoreTransaction(Transaction):
    store = models.ForeignKey('StoreBase.Store', null=True, on_delete=models.SET_NULL)


class HouseOwnerTransaction(Transaction):
    owner = models.ForeignKey('Owners.Owner', null=True, on_delete=models.SET_NULL)


# noinspection PyUnusedLocal
@receiver(pre_save, sender=CustomerTransaction)
def customer_transaction_pre_save_hook(sender, instance, **kwargs):
    old_transaction = CustomerTransaction.objects.filter(id=instance.id).first()
    if not old_transaction:
        return

    # update status of tenant payment (if any)
    if old_transaction.complete is False and instance.complete is True:
        if instance.tenant_payments.count():
            for tenant_payment in instance.tenant_payments.all():
                tenant_payment.status = PAID
                if not tenant_payment.paid_on:
                    tenant_payment.paid_on = timezone.now()
                tenant_payment.save()


# noinspection PyUnusedLocal
@receiver(pre_save, sender=HouseOwnerTransaction)
def house_owner_transaction_pre_save_hook(sender, instance, **kwargs):
    old_transaction = HouseOwnerTransaction.objects.filter(id=instance.id).first()
    if not old_transaction:
        return

    # update status of tenant payment (if any)
    if old_transaction.complete is False and instance.complete is True:
        if instance.owner_payments.count():
            for payment in instance.owner_payments.all():
                payment.status = PAID
                if not payment.paid_on:
                    payment.paid_on = timezone.now()
                payment.save()
