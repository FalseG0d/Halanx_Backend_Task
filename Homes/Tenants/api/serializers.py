from django.utils import timezone
from rest_framework import serializers

from Common.serializers import PaymentCategorySerializer
from Homes.Bookings.models import Booking
from Homes.Houses.models import House
from Homes.Tenants.models import TenantPermanentAddressDetail, TenantCompanyAddressDetail, TenantBankDetail, \
    TenantDocument, Tenant, TenantPayment, TenantRequirement, TenantMoveOutRequest, TenantMeal, TenantLateCheckin
from Transaction.models import CustomerTransaction
from utility.serializer_utils import DisplaySelectedFieldMixin
from utility.serializers import SpaceSerializer, DateTimeFieldTZ, CustomerSerializer, HouseAddressDetailSerializer


class TenantPermanentAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantPermanentAddressDetail
        fields = '__all__'


class TenantCompanyAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantCompanyAddressDetail
        fields = '__all__'


class TenantBankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantBankDetail
        fields = '__all__'


class TenantDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantDocument
        exclude = ('is_deleted', 'verified')


class TenantCurrentBookingSerializer(serializers.ModelSerializer):
    space = SpaceSerializer()
    license_start_date = DateTimeFieldTZ(format='%d %b, %Y')
    license_end_date = DateTimeFieldTZ(format='%d %b, %Y')

    class Meta:
        model = Booking
        fields = '__all__'


class TenantSerializer(serializers.ModelSerializer):
    permanent_address = TenantPermanentAddressDetailSerializer()
    company_address = TenantCompanyAddressDetailSerializer()
    company_joining_date = DateTimeFieldTZ(format='%d %b, %Y', input_formats=['%d-%m-%Y'])
    company_leaving_date = DateTimeFieldTZ(format='%d %b, %Y', input_formats=['%d-%m-%Y'])
    bank_detail = TenantBankDetailSerializer()
    current_stay = serializers.CharField()
    current_booking = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = '__all__'

    @staticmethod
    def get_dob(obj):
        return obj.customer.dob

    def update(self, instance: Tenant, validated_data):
        permanent_address_data = validated_data.pop('permanent_address', None)
        company_address_data = validated_data.pop('company_address', None)
        bank_detail_data = validated_data.pop('bank_detail', None)
        super(self.__class__, self).update(instance, validated_data)
        if permanent_address_data:
            permanent_address_serializer = TenantPermanentAddressDetailSerializer()
            super(TenantPermanentAddressDetailSerializer, permanent_address_serializer) \
                .update(instance.permanent_address, permanent_address_data)
        if company_address_data:
            company_address_serializer = TenantCompanyAddressDetailSerializer()
            super(TenantCompanyAddressDetailSerializer, company_address_serializer) \
                .update(instance.company_address, company_address_data)
        if bank_detail_data:
            bank_detail_serializer = TenantBankDetailSerializer()
            super(TenantBankDetailSerializer, bank_detail_serializer).update(instance.bank_detail, bank_detail_data)
        return instance

    @staticmethod
    def get_current_booking(obj):
        booking = obj.current_booking
        if booking:
            return TenantCurrentBookingSerializer(booking).data


class TenantDetailSerializer(DisplaySelectedFieldMixin, serializers.ModelSerializer):
    customer = CustomerSerializer()
    permanent_address = TenantPermanentAddressDetailSerializer()
    current_stay = serializers.ReadOnlyField()

    class Meta:
        model = Tenant
        fields = '__all__'


class CustomerTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTransaction
        fields = ('id', 'transaction_id', 'payment_gateway')


class TenantPaymentBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantPayment
        fields = '__all__'


class TenantPaymentSerializer(serializers.ModelSerializer):
    category = PaymentCategorySerializer()
    paid_on = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')
    due_date = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')
    transaction = CustomerTransactionSerializer(read_only=True)
    hcash = serializers.SerializerMethodField()

    class Meta:
        model = TenantPayment
        fields = '__all__'

    @staticmethod
    def get_hcash(obj):
        return obj.available_hcash


class TenantFavoriteHousesSerializer(serializers.ModelSerializer):
    address = HouseAddressDetailSerializer()
    rent_from = serializers.ReadOnlyField()
    security_deposit_from = serializers.ReadOnlyField()
    available_flat_count = serializers.ReadOnlyField()
    available_room_count = serializers.ReadOnlyField()
    available_bed_count = serializers.ReadOnlyField()
    accomodation_allowed_str = serializers.ReadOnlyField()
    display_title = serializers.ReadOnlyField()
    furnish_type = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = ('id', 'name', 'address', 'description', 'furnish_type', 'house_size', 'cover_pic_url', 'rent_from',
                  'security_deposit_from', 'available_flat_count', 'available_room_count', 'available_bed_count',
                  'accomodation_allowed_str', 'house_type', 'available_from', 'display_title', 'availability')

    @staticmethod
    def get_availability(obj):
        return list(obj.spaces.values_list('availability', flat=True).distinct())

    @staticmethod
    def get_display_title(obj):
        return obj.display_title

    @staticmethod
    def get_furnish_type(obj):
        return obj.get_furnish_type_display()


class TenantRequirementSerializer(serializers.ModelSerializer):
    expected_movein_date = DateTimeFieldTZ(format='%Y-%m-%d', input_formats=['%d-%m-%Y'], required=False)

    class Meta:
        model = TenantRequirement
        exclude = ('created_at', 'tenant',)


class TenantMoveOutRequestSerializer(serializers.ModelSerializer):
    timing = DateTimeFieldTZ(format='%d %b, %Y')

    class Meta:
        model = TenantMoveOutRequest
        exclude = ('created_at',)

    @staticmethod
    def validate_timing(timings):
        if timings < timezone.now():
            raise serializers.ValidationError('Requested Move out timings must be in future')
        return timings

    @staticmethod
    def validate_tenant(tenant):
        if not tenant.current_booking:
            raise serializers.ValidationError('You don\'t have any booking')
        return tenant


# class TenantMoveInRequestSerializer(serializers.ModelSerializer):
#     timing = DateTimeFieldTZ(format='%d %b, %Y')
#
#     class Meta:
#         model = TenantMoveInRequest
#         exclude = ('created_at', )
#
#     @staticmethod
#     def validate_timing(timings):
#         if timings < timezone.now():
#             raise serializers.ValidationError('Requested Move out timings must be in future')
#         return timings
#
#     @staticmethod
#     def validate_tenant(tenant):
#         if not tenant.current_booking:
#             raise serializers.ValidationError('You don\'t have any booking')
#         return tenant

class TenantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'


class TenantLateCheckInSerializer(serializers.ModelSerializer):
    tenant = serializers.SerializerMethodField()
    expected_checkin = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')

    class Meta:
        model = TenantLateCheckin
        fields = '__all__'

    @staticmethod
    def get_tenant(obj):
        return TenantDetailSerializer(obj.current_booking.tenant, display_fields=['id', 'customer']).data


class TenantMealSerializer(DisplaySelectedFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = TenantMeal
        fields = ('id', 'date', 'type', 'meal', 'house', 'having')
