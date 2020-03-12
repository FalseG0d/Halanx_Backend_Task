from rest_framework import serializers

from Homes.HomeServices.models import ServiceCategory, ServiceRequest, SupportStaffMember, MajorServiceCategory, \
    ServiceRequestImage, SupportStaffMemberWorkAddressDetail, SupportStaffMemberMajorService
from Homes.Tenants.api.serializers import TenantDetailSerializer
from utility.logging_utils import sentry_debug_logger
from utility.render_response_utils import STATUS, ERROR
from utility.serializers import DateTimeFieldTZ


class ServiceCategorySerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = '__all__'

    @staticmethod
    def get_parent(obj):
        return obj.parent.name


class MajorServiceCategoryBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MajorServiceCategory
        fields = '__all__'


class MajorServiceCategorySerializer(MajorServiceCategoryBaseSerializer):
    sub_categories = ServiceCategorySerializer(many=True)


class SupportStaffMemberWorkAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportStaffMemberWorkAddressDetail
        exclude = ('staff_member',)


class SupportStaffMemberSerializer(serializers.ModelSerializer):
    # categories = MajorServiceCategoryBaseSerializer(many=True)
    categories = serializers.SerializerMethodField()
    work_address = SupportStaffMemberWorkAddressDetailSerializer()
    category_create_data = serializers.ListField(write_only=True)

    class Meta:
        model = SupportStaffMember
        fields = '__all__'

    @staticmethod
    def get_categories(obj):
        queryset = obj.categories
        return MajorServiceCategoryBaseSerializer(queryset, many=True).data

    @staticmethod
    def validate_category_create_data(category_create_data_id_list):
        if category_create_data_id_list:
            for category_id in category_create_data_id_list:
                try:
                    _ = MajorServiceCategory.objects.get(id=category_id)
                except Exception as E:
                    raise serializers.ValidationError(E)

        return category_create_data_id_list

    def create(self, validated_data):
        # remove nested writes
        address_data = validated_data.pop('work_address', None)
        category_create_data_id_list = validated_data.pop('category_create_data', None)
        # create main object
        instance = super(self.__class__, self).create(validated_data)

        if address_data:
            address_serializer = SupportStaffMemberWorkAddressDetailSerializer()
            # updating address object since address was created automatically
            super(SupportStaffMemberWorkAddressDetailSerializer, address_serializer).update(instance.work_address,
                                                                                            address_data)

        if category_create_data_id_list:
            for category_id in category_create_data_id_list:
                major_service_category = MajorServiceCategory.objects.get(id=category_id)
                SupportStaffMemberMajorService.objects.create(staff_member=instance, category=major_service_category)

        return instance

    def update(self, instance, validated_data):
        work_address_data = validated_data.pop('work_address', None)
        category_create_data_id_list = validated_data.pop('category_create_data', None)

        super(self.__class__, self).update(instance, validated_data)
        if work_address_data:
            work_address_detail_serializer = SupportStaffMemberWorkAddressDetailSerializer()
            super(SupportStaffMemberWorkAddressDetailSerializer, work_address_detail_serializer).update(
                instance.work_address,
                work_address_data)

        if category_create_data_id_list is not None:
            for category_id in category_create_data_id_list:
                    category = MajorServiceCategory.objects.get(id=category_id)
                    SupportStaffMemberMajorService.objects.get_or_create(staff_member=instance, category=category)

            instance.staff_services.exclude(category__id__in=category_create_data_id_list).delete()

        return instance


class ServiceRequestBaseSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer()
    tenant = serializers.SerializerMethodField()

    @staticmethod
    def get_tenant(obj):
        return TenantDetailSerializer(obj.booking.tenant, display_fields=['permanent_adress', 'customer', 'id']).data

    class Meta:
        model = ServiceRequest
        fields = '__all__'

    def create(self, validated_data):
        if 'booking' not in validated_data:
            raise serializers.ValidationError({STATUS: ERROR, "message": 'booking required'})

        if validated_data['booking'].tenant == validated_data['booking'].tenant.current_booking:
            raise serializers.ValidationError({STATUS: ERROR, "message": 'booking invalid'})

        return super(ServiceRequestBaseSerializer, self).create(validated_data)


class ServiceRequestSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer()
    support_staff_member = SupportStaffMemberSerializer()
    created_at = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')
    modified_at = DateTimeFieldTZ(format='%d %b, %Y %I:%M %p')
    space = serializers.SerializerMethodField()
    added_by = serializers.SerializerMethodField()
    tenant = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = '__all__'

    @staticmethod
    def get_tenant(obj):
        try:
            return TenantDetailSerializer(obj.booking.tenant).data
        except Exception as E:
            sentry_debug_logger.error(E, exc_info=True)
            return None

    @staticmethod
    def get_space(obj):
        if obj.booking:
            return obj.booking.space.name
        else:
            return None

    def get_added_by(self, obj):
        user = self.context['request'].user
        if obj.booking and obj.booking.tenant and obj.booking.tenant.customer and obj.booking.tenant.customer.user:
            if obj.booking.tenant.customer.user == user:
                return 'me'
            else:
                return obj.booking.tenant.name

        return None


class ServiceRequestCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = ('id', 'category', 'problem')


class ServiceRequestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequestImage
        fields = ('id', 'image')
