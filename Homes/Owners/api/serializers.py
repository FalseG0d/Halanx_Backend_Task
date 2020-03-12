from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from Common.serializers import PaymentCategorySerializer
from Homes.Bookings.models import Booking
from Homes.Houses.api.serializers import OccupationSerializer
from Homes.Houses.models import House, ExistingFacility, Bill, BillSplit
from Homes.Owners.models import Owner, OwnerAddressDetail, OwnerBankDetail, OwnerDocument, OwnerPayment, \
    OwnerNotificationImage, OwnerNotification, OwnerWallet, WithdrawalRequest, OwnerListing, TeamMember, Vendor, \
    TenantGroup
from utility.serializers import DateTimeFieldTZ
from utility.time_utils import get_natural_datetime


class OwnerAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerAddressDetail
        fields = '__all__'


class OwnerBankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerBankDetail
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')


class OwnerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    dob = serializers.DateField(format="%d %B, %Y", input_formats=["%Y-%m-%d"])
    address = OwnerAddressDetailSerializer()
    bank_detail = OwnerBankDetailSerializer()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Owner
        fields = '__all__'

    @staticmethod
    def get_balance(obj):
        return obj.wallet.balance

    def update(self, instance: Owner, validated_data):
        # remove non-updatable fields
        validated_data.pop('verified', None)
        # nested data
        user_data = validated_data.pop('user', None)
        address_data = validated_data.pop('address', None)
        bank_detail_data = validated_data.pop('bank_detail', None)
        super(self.__class__, self).update(instance, validated_data)
        if address_data:
            address_serializer = OwnerAddressDetailSerializer()
            super(OwnerAddressDetailSerializer, address_serializer) \
                .update(instance.address, address_data)
        if bank_detail_data:
            bank_detail_serializer = OwnerBankDetailSerializer()
            super(OwnerBankDetailSerializer, bank_detail_serializer).update(instance.bank_detail, bank_detail_data)
        if user_data:
            user_serializer = UserSerializer()
            super(UserSerializer, user_serializer).update(instance.user, user_data)
        return instance


class OwnerHouseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ('id', 'name', 'visible', 'cover_pic_url')


class OwnerHouseDetailSerializer(OwnerHouseListSerializer):
    accomodation_allowed_str = serializers.ReadOnlyField()
    agreement_commencement_date = DateTimeFieldTZ(format='%d %b, %Y')

    class Meta:
        model = House
        fields = ('id', 'name', 'visible', 'cover_pic_url', 'accomodation_allowed_str', 'agreement_commencement_date')


class OwnerHouseExistingFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExistingFacility
        fields = '__all__'


class OwnerHouseBookingSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    monthly_rent = serializers.SerializerMethodField()
    license_start_date = DateTimeFieldTZ(format='%d %b, %Y')
    license_end_date = DateTimeFieldTZ(format='%d %b, %Y')

    class Meta:
        model = Booking
        fields = ('id', 'tenant_name', 'license_start_date', 'license_end_date', 'moved_out', 'monthly_rent')

    @staticmethod
    def get_tenant_name(obj):
        return obj.tenant.name

    @staticmethod
    def get_monthly_rent(obj):
        return obj.monthly_rents.last().rent


class OwnerWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerWallet
        fields = ('id', 'balance')


class OwnerPaymentSerializer(serializers.ModelSerializer):
    category = PaymentCategorySerializer()
    paid_on = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')

    class Meta:
        model = OwnerPayment
        fields = ('id', 'category', 'type', 'paid_on', 'amount', 'description')


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    created_at = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p', read_only=True)
    status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WithdrawalRequest
        fields = '__all__'

    @staticmethod
    def get_status(obj):
        return obj.status


class OwnerNotificationListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = OwnerNotification
        fields = ('owner', 'category', 'content', 'timestamp', 'image')

    @staticmethod
    def get_image(obj):
        notif_image = OwnerNotificationImage.objects.filter(category=obj.category).first()
        return notif_image.image.url if notif_image else None

    @staticmethod
    def get_timestamp(obj):
        return get_natural_datetime(obj.timestamp)


class OwnerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerDocument
        exclude = ('is_deleted',)


class OwnerListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerListing
        exclude = ('created_at', 'referrer_tenant', 'referrer_owner', 'owner')


class TeamMemberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        exclude = ('owner',)

    def validate_houses(self, houses):
        for house in houses:
            if house.owner != self.context['owner']:
                raise ValidationError({'detail': "House with id {} does not exist".format(house.id)})
        return houses

    def create(self, validated_data):
        validated_data['owner'] = self.context['owner']
        return super(TeamMemberCreateSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('owner', None)
        return super(TeamMemberCreateSerializer, self).update(instance, validated_data)


class VendorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        exclude = ('owner',)

    def validate_houses(self, houses):
        for house in houses:
            if house.owner != self.context['owner']:
                raise ValidationError({'detail': "House with id {} does not exist".format(house.id)})

        return houses

    def create(self, validated_data):
        validated_data['owner'] = self.context['owner']
        return super(VendorCreateSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('owner', None)
        return super(VendorCreateSerializer, self).update(instance, validated_data)


class VendorSerializer(VendorCreateSerializer):
    occupation = OccupationSerializer()


class BillCreateSerializer(serializers.ModelSerializer):
    created_at = DateTimeFieldTZ('%d %B, %Y %I:%M %p', read_only=True)
    modified_at = DateTimeFieldTZ('%d %B, %Y %I:%M %p', read_only=True)

    class Meta:
        model = Bill
        exclude = ('owner',)


class TenantGroupCreateSerializer(serializers.ModelSerializer):
    created_at = DateTimeFieldTZ('%d %B, %Y %I:%M %p', read_only=True)
    modified_at = DateTimeFieldTZ('%d %B, %Y %I:%M %p', read_only=True)

    class Meta:
        model = TenantGroup
        exclude = ('owner',)


class BillSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillSplit
        fields = '__all__'