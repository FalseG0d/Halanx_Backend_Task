import logging

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from Homes.Houses.models import Space, House, HouseAddressDetail
from Places.models import Place
from StoreBase.models import Store
from UserBase.models import Customer

logger = logging.getLogger(__name__)


class DateTimeFieldTZ(serializers.DateTimeField):
    def to_representation(self, value):
        try:
            value = timezone.localtime(value)
            return super(DateTimeFieldTZ, self).to_representation(value)
        except Exception as e:
            logger.error(e)


class RupeeInTextField(serializers.CharField):
    def to_representation(self, value):
        value = value.replace('Rs. ', '₹')
        return super(RupeeInTextField, self).to_representation(value)


class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class CustomerSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()

    class Meta:
        model = Customer
        fields = ('id', 'user', 'profile_pic_url', 'phone_no')


class HalanxCustomerSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    following = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ('id', 'user', 'profile_pic_url', 'following')

    def get_following(self, halanx_user):
        if halanx_user in self.context['customer'].follows.all():
            return True
        else:
            return False


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'category', 'store_logo_url', 'place')


class PlaceTileSerializer(serializers.ModelSerializer):
    offer = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    store_logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ('id', 'store', 'name', 'city', 'rating', 'cover_pic_url', 'store_logo_url',
                  'is_open', 'highlights', 'offer')

    @staticmethod
    def get_store_logo_url(obj):
        if hasattr(obj, 'store'):
            return obj.store.store_logo_url

    @staticmethod
    def get_offer(obj):
        if hasattr(obj, 'store') and obj.store.plans.filter(name='A').count():
            return "{}% cashback, upto ₹{}".format(obj.store.hcash_percentage, obj.store.hcash_limit)

    @staticmethod
    def get_rating(obj):
        return round(obj.rating, 1)


class HouseAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseAddressDetail
        exclude = ('house',)


class HouseBasicSerializer(serializers.ModelSerializer):
    address = HouseAddressDetailSerializer()
    display_title = serializers.SerializerMethodField()

    class Meta:
        model = House
        exclude = ('owner', 'rules', 'created_at', 'modified_at', 'visible')

    @staticmethod
    def get_display_title(obj):
        return obj.display_title


class SpaceSerializer(serializers.ModelSerializer):
    house = HouseBasicSerializer()

    class Meta:
        model = Space
        fields = ('id', 'name', 'house', 'rent', 'security_deposit')


# noinspection PyAbstractClass
class TimeSlotSerializer(serializers.Serializer):
    date = serializers.DateField(format="%d %B %Y")
    time = serializers.ListField(
        child=serializers.TimeField(format="%I:%M %p")
    )
