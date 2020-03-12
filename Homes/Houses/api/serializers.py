from django.db.models import Sum
from rest_framework import serializers
from rest_framework.fields import MultipleChoiceField
from rest_framework.generics import get_object_or_404

from Homes.AreaManagers.models import AreaManager
from Homes.Houses.models import (House, Flat, SharedRoom, PrivateRoom, HousePicture, HouseVisit, HouseAmenity, Amenity,
                                 Bed, SubAmenity, Space, HouseApplicationAddressDetail,
                                 HouseApplication, HouseMonthlyExpense, MonthlyExpenseCategory, SpaceSubType,
                                 HouseSearchSlug, PopularLocation, Occupation, BillCategory)
from Homes.Houses.utils import INHOUSE_AMENITY, SOCIETY_AMENITY, get_house_visit_time_slots, AVAILABLE, \
    HouseAccomodationAllowedCategories, HouseAccomodationTypeCategories
from Homes.Owners.models import Owner
from Homes.Tenants.models import Tenant
from UserBase.models import Customer
from utility.serializer_utils import DisplayFieldsMixin
from utility.serializers import DateTimeFieldTZ, JSONSerializerField, TimeSlotSerializer, \
    HouseAddressDetailSerializer, HouseBasicSerializer


class HouseApplicationAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseApplicationAddressDetail
        exclude = ('application',)


class HousePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousePicture
        exclude = ('house',)


class MonthlyExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyExpenseCategory
        fields = '__all__'


class HouseMonthlyExpenseSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()

    class Meta:
        model = HouseMonthlyExpense
        fields = '__all__'

    @staticmethod
    def get_category(obj):
        return obj.category.name


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'


class SubAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubAmenity
        fields = '__all__'


class HouseAmenitySerializer(serializers.ModelSerializer):
    amenity = AmenitySerializer()
    sub_amenities = SubAmenitySerializer(many=True)

    class Meta:
        model = HouseAmenity
        fields = '__all__'


class OwnerBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = ('name', 'profile_pic')


class SpaceSubTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceSubType
        fields = '__all__'


class SpaceSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    monthly_expenses = serializers.SerializerMethodField()  # deprecated
    subtype = SpaceSubTypeSerializer()

    class Meta:
        model = Space
        exclude = ('visible', 'commission',)

    @staticmethod
    def get_name(obj):
        """
        provide subtype name as space name
        """
        return obj.subtype.name

    # noinspection PyUnusedLocal
    @staticmethod
    def get_monthly_expenses(obj):
        return []


class SpaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        exclude = ('visible', 'commission',)
        extra_kwargs = {'subtype': {'required': True}}

    def update(self, instance, validated_data):
        # check if updated House belongs to the logged in owner
        if validated_data.get("house", None):
            get_object_or_404(House, id=validated_data["house"].id, owner=self.context["owner"])

        return super(SpaceCreateSerializer, self).update(instance, validated_data)


class PrivateRoomSerializer(serializers.ModelSerializer):
    space = SpaceSerializer()

    class Meta:
        model = PrivateRoom
        fields = '__all__'


class BedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bed
        exclude = ('visible',)


class SharedRoomSerializer(serializers.ModelSerializer):
    space = SpaceSerializer()
    beds = serializers.SerializerMethodField()
    bed_count = serializers.IntegerField()
    free_bed_count = serializers.IntegerField()

    class Meta:
        model = SharedRoom
        fields = '__all__'

    @staticmethod
    def get_beds(obj):
        return BedSerializer(obj.beds.filter(visible=True), many=True).data


class FlatSerializer(serializers.ModelSerializer):
    space = SpaceSerializer()

    class Meta:
        model = Flat
        fields = '__all__'


class HouseListSerializer(serializers.ModelSerializer):
    address = HouseAddressDetailSerializer()
    rent_from = serializers.ReadOnlyField()
    security_deposit_from = serializers.ReadOnlyField()
    available_flat_count = serializers.ReadOnlyField()
    available_room_count = serializers.ReadOnlyField()
    available_bed_count = serializers.ReadOnlyField()
    accomodation_allowed_str = serializers.ReadOnlyField()
    favorited = serializers.SerializerMethodField()
    house_type = serializers.SerializerMethodField()
    furnish_type = serializers.SerializerMethodField()
    bhk_count = serializers.ReadOnlyField()

    display_title = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = ('id', 'name', 'address', 'description', 'furnish_type', 'house_size', 'cover_pic_url', 'rent_from',
                  'security_deposit_from', 'available_flat_count', 'available_room_count', 'available_bed_count',
                  'accomodation_allowed_str', 'house_type', 'available_from', 'favorited', 'display_title',
                  'availability', 'average_rating', 'bhk_count')

    @staticmethod
    def get_availability(obj):
        return list(obj.spaces.values_list('availability', flat=True).distinct())

    def get_favorited(self, obj):
        user = self.context['request'].user
        tenant = Tenant.objects.filter(customer__user=user).first() if user.is_authenticated else None
        return obj in tenant.favorite_houses.all() if tenant else False

    @staticmethod
    def get_house_type(obj):
        return obj.get_house_type_display()

    @staticmethod
    def get_furnish_type(obj):
        return obj.get_furnish_type_display()

    @staticmethod
    def get_display_title(obj):
        return obj.display_title

    @staticmethod
    def get_average_rating(obj):
        house_visits = HouseVisit.objects.filter(house=obj, visited=True)
        if house_visits:
            return house_visits.aggregate(Sum('customer_rating'))['customer_rating__sum']
        else:
            return None


class HouseDetailSerializer(HouseListSerializer):
    owner = OwnerBasicSerializer()
    pictures = HousePictureSerializer(many=True)
    monthly_expenses = HouseMonthlyExpenseSerializer(many=True)
    rent_included_expenses = MonthlyExpenseCategorySerializer(many=True)
    rent_excluded_expenses = MonthlyExpenseCategorySerializer(many=True)
    inhouse_amenities = serializers.SerializerMethodField()
    society_amenities = serializers.SerializerMethodField()

    private_rooms = serializers.SerializerMethodField()
    shared_rooms = serializers.SerializerMethodField()
    flats = serializers.SerializerMethodField()
    visit_time_slots = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()

    visit_status = serializers.SerializerMethodField()
    visit_details = serializers.SerializerMethodField()

    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = House
        exclude = ('created_at', 'modified_at', 'visible', 'application')

    @staticmethod
    def get_inhouse_amenities(obj):
        return HouseAmenitySerializer(obj.amenities.filter(amenity__category=INHOUSE_AMENITY), many=True).data

    @staticmethod
    def get_society_amenities(obj):
        return HouseAmenitySerializer(obj.amenities.filter(amenity__category=SOCIETY_AMENITY), many=True).data

    @staticmethod
    def get_sample_rooms(all_rooms):
        subtype_ids = all_rooms.values_list('space__subtype', flat=True).distinct()
        sample_rooms = []
        for subtype_id in subtype_ids:
            rooms = all_rooms.filter(space__subtype__id=subtype_id)
            if any([room.space.availability == AVAILABLE for room in rooms]):
                sample_rooms.append(rooms.filter(space__availability=AVAILABLE).first())
            else:
                sample_rooms.append(rooms.first())
        return list(filter(lambda x: x is not None, sample_rooms))

    def get_private_rooms(self, obj):
        private_rooms = self.get_sample_rooms(obj.private_rooms.filter(space__visible=True))
        return PrivateRoomSerializer(private_rooms, many=True).data

    def get_shared_rooms(self, obj):
        shared_rooms = self.get_sample_rooms(obj.shared_rooms.filter(space__visible=True))
        return SharedRoomSerializer(shared_rooms, many=True).data

    @staticmethod
    def get_flats(obj):
        return FlatSerializer(obj.flats.filter(space__visible=True), many=True).data

    @staticmethod
    def get_visit_time_slots(obj):
        time_slots = get_house_visit_time_slots(obj)
        return TimeSlotSerializer(time_slots, many=True).data

    def get_visit_status(self, obj):
        try:
            if self.context['request'].user.is_authenticated:
                tenant = Tenant.objects.filter(customer__user=self.context['request'].user).first()
                house_visits = obj.visits.filter(customer=tenant.customer, cancelled=False)
                if house_visits:
                    return True
                else:
                    return False

        except Exception as E:
            print(E)
            return None

    def get_visit_details(self, obj):
        try:
            if self.context['request'].user.is_authenticated:
                tenant = Tenant.objects.filter(customer__user=self.context['request'].user).first()
                house_visits = obj.visits.filter(customer=tenant.customer, cancelled=False)
                if house_visits:
                    return HouseVisitSerializer(house_visits.last()).data
                else:
                    return None

        except Exception as E:
            print("error in getting visit details is " + str(E))
            return None

    @staticmethod
    def get_display_title(obj):
        return obj.display_title

    @staticmethod
    def get_average_rating(obj):
        house_visits = HouseVisit.objects.filter(house=obj, visited=True)
        if house_visits:
            return house_visits.aggregate(Sum('customer_rating'))['customer_rating__sum']
        else:
            return None


class HouseCreateSerializer(DisplayFieldsMixin, serializers.ModelSerializer):
    available_accomodation_types = MultipleChoiceField(choices=HouseAccomodationTypeCategories, required=False)
    accomodation_allowed = MultipleChoiceField(choices=HouseAccomodationAllowedCategories, required=False)
    address = HouseAddressDetailSerializer()

    class Meta:
        model = House
        exclude = ('preferred_food', 'agreement_commencement_date',
                   'created_at', 'modified_at', 'available_from', 'visible', 'application', 'area_managers', 'owner')

    def create(self, validated_data):
        # remove nested writes
        address_data = validated_data.pop('address', None)

        # create main object
        instance = super(self.__class__, self).create(validated_data)

        if address_data:
            address_serializer = HouseAddressDetailSerializer()
            # updating address object since address was created automatically
            super(HouseAddressDetailSerializer, address_serializer). \
                update(instance.address, address_data)

        return instance

    def update(self, instance: House, validated_data):
        # remove nested writes
        address_data = validated_data.pop('address', None)

        # update main object
        instance = super(self.__class__, self).update(instance, validated_data)

        if address_data:
            address_serializer = HouseAddressDetailSerializer()
            # updating address object
            super(HouseAddressDetailSerializer, address_serializer). \
                update(instance.address, address_data)

        return instance


class HouseVisitTimeSlotSerializer(serializers.ModelSerializer):
    visit_time_slots = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = ('id', 'visit_time_slots')

    @staticmethod
    def get_visit_time_slots(obj):
        time_slots = get_house_visit_time_slots(obj)
        return TimeSlotSerializer(time_slots, many=True).data


class HouseVisitSerializer(serializers.ModelSerializer):
    scheduled_visit_time = DateTimeFieldTZ(format='%d %B %Y %I:%M %p', input_formats=['%d %B %Y %I:%M %p'])

    class Meta:
        model = HouseVisit
        fields = '__all__'


class CustomerBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('name', 'profile_pic_url')


class AreaManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaManager
        fields = ('name', 'phone_no', 'profile_pic')


class HouseVisitListSerializer(serializers.ModelSerializer):
    house = HouseBasicSerializer()
    customer = CustomerBasicSerializer()
    area_manager = AreaManagerSerializer()
    scheduled_visit_time = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')
    actual_visit_time = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')

    class Meta:
        model = HouseVisit
        fields = '__all__'


class HouseApplicationSerializer(serializers.ModelSerializer):
    address = HouseApplicationAddressDetailSerializer(required=False)
    accomodation_allowed = JSONSerializerField()

    class Meta:
        model = HouseApplication
        fields = '__all__'

    def create(self, validated_data):
        # find address data
        address_data = validated_data.pop('address')

        # create house application
        application = HouseApplication.objects.create(**validated_data)

        # set house application address
        serializer = HouseApplicationAddressDetailSerializer(application.address, data=address_data, partial=True)
        if serializer.is_valid():
            serializer.update(application.address, address_data)

        # set new house details
        house = application.house.get()
        fields_to_copy = ['house_type', 'furnish_type', 'accomodation_allowed', 'bhk_count']
        house_data = {}
        for field in fields_to_copy:
            house_data[field] = validated_data[field]
        serializer = HouseBasicSerializer(house, data=house_data, partial=True)
        if serializer.is_valid():
            house = serializer.update(house, house_data)

        # set new house address details
        serializer = HouseAddressDetailSerializer(house.address, data=address_data, partial=True)
        if serializer.is_valid():
            serializer.update(house.address, address_data)

        return application


class HouseSearchSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseSearchSlug
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(HouseSearchSlugSerializer, self).__init__(*args, **kwargs)

        fields = self.context['fields']
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class PopularLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopularLocation
        fields = '__all__'


class OccupationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occupation
        fields = "__all__"


class BillCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BillCategory
        fields = '__all__'


