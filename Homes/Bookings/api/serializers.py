from rest_framework import serializers

from Homes.Bookings.models import Booking, AdvanceBooking, BookingFacility
from Homes.Bookings.models import FacilityItem, BookingMoveInDigitalSignature
from Homes.Houses.api.serializers import HouseVisitSerializer
from Homes.Houses.models import HouseVisit
from Homes.Tenants.api.serializers import TenantPaymentSerializer
from Homes.Tenants.utils import get_tenant_profile_completion
from utility.serializers import SpaceSerializer, DateTimeFieldTZ, JSONSerializerField


class FacilityItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityItem
        fields = '__all__'


class BookingFacilitySerializer(serializers.ModelSerializer):
    item = FacilityItemSerializer()

    class Meta:
        model = BookingFacility
        exclude = ('booking', 'remark', 'status')


class BookingFacilityUpdateQuantityAcknowledgementAtMoveInSerializer(serializers.ModelSerializer):
    item = FacilityItemSerializer()

    class Meta:
        model = BookingFacility
        fields = ('quantity_acknowledged',)


class BookingDetailSerializer(serializers.ModelSerializer):
    space = SpaceSerializer()
    payments = TenantPaymentSerializer(many=True)
    total_amount = serializers.SerializerMethodField()
    facilities = BookingFacilitySerializer(many=True)
    agreement_verification_status = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    @staticmethod
    def get_total_amount(obj):
        return round(obj.token_amount + obj.movein_charges, 2)

    @staticmethod
    def get_agreement_verification_status(obj):
        return {'code': obj.agreement_verification_status, 'display': obj.get_agreement_verification_status_display()}


class BookingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'


class AdvanceBookingCreateSerializer(serializers.ModelSerializer):
    accomodation_for = JSONSerializerField()

    class Meta:
        model = AdvanceBooking
        exclude = ('cancelled', 'space_type')


class AdvanceBookingDetailSerializer(serializers.ModelSerializer):
    expected_movein_date = serializers.DateField(format="%d %b, %Y", input_formats=['%d-%m-%Y'])
    created_at = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')
    modified_at = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')
    space_subtype = serializers.SerializerMethodField()
    accomodation_for = serializers.SerializerMethodField()

    class Meta:
        model = AdvanceBooking
        fields = '__all__'

    @staticmethod
    def get_space_subtype(obj):
        return obj.space_subtype.name

    @staticmethod
    def get_space_type(obj):
        return obj.get_space_type_display()

    @staticmethod
    def get_accomodation_for(obj):
        return obj.accomodation_for_str


class BookingMoveInDigitalSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingMoveInDigitalSignature
        fields = '__all__'


class TenantTimeLineSerializer(serializers.Serializer):
    house_visits = serializers.SerializerMethodField()
    booking = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def get_house_visits(self, tenant):
        house_visits = HouseVisit.objects.filter(customer__tenant=tenant, house__owner=self.context['owner'])
        if house_visits:
            house_visit_serializer = HouseVisitSerializer(house_visits, many=True)
            return house_visit_serializer.data
        else:
            return None

    def get_booking(self, tenant):
        booking = Booking.objects.filter(tenant=tenant, space__house__owner=self.context['owner']).last()
        if booking:
            booking_serializer = BookingDetailSerializer(booking)
            booking_serializer_data = booking_serializer.data
            booking_facilities = booking.facilities.all()
            booking_serializer_data['assigned_items'] = BookingFacilitySerializer(booking_facilities, many=True).data
            return booking_serializer_data
        else:
            return None

    @staticmethod
    def get_profile(tenant):
        tenant_profile_missing_fields, tenant_profile_completion_percentage = get_tenant_profile_completion(tenant)
        return {
            'completion_percentage': tenant_profile_completion_percentage,
            'missing_fields': tenant_profile_missing_fields
        }
