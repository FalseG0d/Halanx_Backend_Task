from django.contrib.auth import get_user_model

User = get_user_model()

DocumentTypeCategories = (
    ('Id', 'Id'),
    ('Employment', 'Employment'),
    ('PAN', 'PAN'),
    ('Electricity', 'Electricity'),
    ('Water', 'Water'),
    ('Maintenance', 'Maintenance'),
    ('Insurance', 'Insurance'),
    ('Agreement', 'Agreement'),
    ('Others', 'Others'),
    ('Aadhaar', 'Aadhaar'),
    ('MyPhoto', 'MyPhoto'),
)


WEB_PLATFORM = 'web'
ANDROID_PLATFORM = 'android'
IOS_PLATFORM = 'ios'
PlatformChoices = (
    (WEB_PLATFORM, WEB_PLATFORM),
    (ANDROID_PLATFORM, ANDROID_PLATFORM),
    (IOS_PLATFORM, IOS_PLATFORM),
)


PAID = "paid"
PENDING = "pending"
CANCELLED = "cancelled"

PaymentStatusCategories = (
    (PAID, "Paid"),
    (PENDING, "Pending"),
    (CANCELLED, "Cancelled")
)


WITHDRAWAL = "withdrawal"
DEPOSIT = "deposit"

PaymentTypeCategories = (
    (WITHDRAWAL, "Withdrawal"),
    (DEPOSIT, "Deposit")
)

GST_PERCENTAGE = 18


def get_payment_category_icon_upload_path(instance, filename):
    return "Payment/Category/{}/{}".format(instance.id, filename.split('/')[-1])


def get_halanx_user():
    return User.objects.get_or_create(username='halanx', is_staff=True)[0]
