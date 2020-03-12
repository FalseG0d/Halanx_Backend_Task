from datetime import datetime

from rest_framework import serializers

from Carts.models import GroupCart, Cart
from Products.models import Product
from UserBase.models import Customer, Work, Education, UserInterest, Contact, Picture
from utility.serializers import DateTimeFieldTZ, AuthUserSerializer, StoreSerializer


def get_active_group_cart(customer):
    cart, _ = Cart.objects.get_or_create(customer=customer)
    return customer.cart.active_group_cart


class GroupCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupCart
        fields = '__all__'


class PublicUserSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    dob = serializers.DateField(format="%d %B, %Y", input_formats=['%d-%m-%Y'])
    following_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    work = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    group_cart = serializers.SerializerMethodField()
    notification_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        exclude = ('favorite_items', 'favorite_places', 'user_interests', 'phone_no', 'account_balance',
                   'hcash', 'referrer', 'referral_code', 'subscription_total', 'dlatitude', 'dlongitude',
                   'clatitude', 'clongitude', 'gcm_id', 'access_token', 'app_version', 'receive_notification',
                   'is_visible', 'follows', 'last_visit', 'is_registered', 'fb_template', 'is_email_verified',
                   'notification_count')

    def get_is_followed(self, obj):
        return bool(obj.followed_by.filter(user=self.context['request'].user).count())

    @staticmethod
    def get_following_count(obj):
        return obj.follows.count()

    @staticmethod
    def get_followers_count(obj):
        return obj.followed_by.count()

    @staticmethod
    def get_work(obj):
        return WorkSerializer(Work.objects.filter(customer=obj).order_by('-from_year', '-id'), many=True).data

    @staticmethod
    def get_education(obj):
        return EducationSerializer(Education.objects.filter(customer=obj
                                                            ).order_by('-from_year', '-id'), many=True).data

    @staticmethod
    def get_group_cart(obj):
        group_cart = get_active_group_cart(obj)
        return GroupCartSerializer(group_cart).data if group_cart else None

    @staticmethod
    def get_notification_count(obj):
        return obj.notifications.filter(seen=False, display=True).count()


class UserSerializer(PublicUserSerializer):
    group_cart = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        exclude = ('last_visit', 'gcm_id', 'user_interests', 'favorite_items',
                   'favorite_places', 'follows', 'is_registered', 'is_followed')

    @staticmethod
    def get_group_cart(obj):
        group_cart = get_active_group_cart(obj)
        return GroupCartSerializer(group_cart).data if group_cart else None

    @staticmethod
    def get_email(obj):
        return obj.user.email

    @staticmethod
    def get_dob(obj):
        if obj.dob is not None:
            dob = datetime.strptime(obj.dob, "%Y-%m-%d") if type(obj.dob) == str else obj.dob
            return dob.strftime('%d %B, %Y')


class UserFollowerListSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    following = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ('id', 'user', 'bio', 'profile_pic_thumbnail_url', 'following')

    def get_following(self, obj):
        me = self.context.get('me')
        return obj in me.follows.all()


class UserInterestListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        customer = Customer.objects.get(user=self.context.get('user'))
        new_interests = UserInterest.objects.filter(id__in=[row['id'] for row in validated_data])
        customer.user_interests.set(new_interests, clear=True)
        return customer.user_interests.all()


class UserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterest
        exclude = ('sub_interests',)
        list_serializer_class = UserInterestListSerializer


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'


class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = '__all__'


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class PictureSerializer(serializers.ModelSerializer):
    timestamp = DateTimeFieldTZ(read_only=True)

    class Meta:
        model = Picture
        exclude = ('is_deleted',)


class UserProfileSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    distance = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ('user', 'id', 'bio', 'profile_pic_thumbnail_url', 'distance', 'age', 'following')

    def get_distance(self, obj):
        d = self.context['distance'][obj.id]
        ans = '{:.1f} km away'.format(d / 1000) if d >= 1000 else '{} m away'.format(int(d))
        return ans

    def get_following(self, halanx_user):
        try:
            if halanx_user in self.context['customer'].follows.all():
                return True
            else:
                return False
        except:
            return None


class ProductSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'store', 'name', 'mrp', 'price', 'tax', 'category', 'product_image_url')
