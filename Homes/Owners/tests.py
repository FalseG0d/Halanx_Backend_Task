# Create your tests here.
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from UserBase.models import Customer
User = get_user_model()


class OwnerTestCase(APITestCase):

    def setUp(self):
        print(self.client)