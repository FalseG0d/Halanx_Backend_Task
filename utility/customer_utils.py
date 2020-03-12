import random

from django.contrib.auth import get_user_model

from UserBase.models import Customer

User = get_user_model()


def delete_customer(customer_id):
    customer = Customer.objects.get(id=customer_id)
    customer.tenant.wallet.delete()
    customer.tenant.delete()
    user = customer.user
    customer.delete()
    user.delete()


def create_customer(first_name, last_name, phone_no, password=None):
    if password is None:
        password = str(random.randint(10000, 100000))
    username = 'c{}'.format(phone_no)
    user = User.objects.create(username=username, first_name=first_name, last_name=last_name,
                               password=password)
    Customer.objects.create(user=user, phone_no=phone_no)


def create_demo_customer():
    create_customer('Nikhil', 'Kumar', '8920658574', 'abcd@1234')


def is_customer_registered(phone_no):
    try:
        phone_no = phone_no.replace(" ", "")
        is_exist = Customer.objects.get(phone_no=phone_no, is_registered=True)
        return is_exist
    except Exception as e:
        return None


def is_customer_exist(phone_no):
    try:
        phone_no = phone_no.replace(" ", "")
        is_exist = Customer.objects.get(phone_no=phone_no)
        return is_exist
    except Exception as e:
        return None


