# Create your views here.
import datetime
import random

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateAPIView, \
    get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from Homes.Bookings.models import Booking
from Homes.Bookings.utils import BOOKING_COMPLETE
from Homes.HomeServices.api.serializers import ServiceRequestSerializer, MajorServiceCategorySerializer, \
    ServiceCategorySerializer, ServiceRequestBaseSerializer, \
    SupportStaffMemberSerializer
from Homes.HomeServices.models import ServiceRequest, MajorServiceCategory, ServiceCategory, SupportStaffMember
from Homes.HomeServices.utils import ServiceRequestStatusCategories
from Homes.Houses.api.serializers import HouseDetailSerializer
from Homes.Houses.models import House
from Homes.Houses.utils import get_house_url_from_house_id
from Homes.OperationManagers.api.serializers import ServiceRequestCreateSerializer
from Homes.OperationManagers.utils import HOUSE_LIST_DETAILS_MSG
from Homes.Tenants.api.serializers import TenantPaymentSerializer, TenantDetailSerializer, \
    TenantPaymentBaseSerializer
from Homes.Tenants.models import TenantPayment, Tenant
from Homes.permissions import IsOperationManager
from MobileMessage.models import MobileMessage
from utility.pagination_utils import StandardPagination
from utility.query_utils import get_filter_extra_kwargs
from utility.render_response_utils import STATUS, SUCCESS, ERROR, DATA


class ServiceRequestPageDataView(GenericAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsOperationManager, ]

    def get(self, request, *args, **kwargs):
        data = dict()
        data['Categories'] = MajorServiceCategorySerializer(MajorServiceCategory.objects.all(), many=True).data
        data['SubCategories'] = ServiceCategorySerializer(ServiceCategory.objects.all(), many=True).data
        data['Status'] = [i[0] for i in ServiceRequestStatusCategories]
        return Response(data)


class ServiceRequestListView(ListCreateAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsOperationManager, ]
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = ServiceRequest.objects.all()
        query_filter_params = {
            'category__name__in': 'category',
            'category__parent__name__in': 'parent_category',
            'status__in': 'status',
            'created_at__gte': 'from_date',
            'created_at__lte': 'to_date',
            'support_staff_member__id__in': 'support_staff_member',
        }
        list_filter_dict = {
            'category__name__in': {},
            'category__parent__name__in': {},
            'status__in': {},
            'support_staff_member__id__in': {}}
        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request, list_filter_dict=list_filter_dict)
        queryset = queryset.filter(**extra_kwargs)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ServiceRequestSerializer
        else:
            return ServiceRequestCreateSerializer


class ServiceRequestRetrieveUpdateView(RetrieveUpdateAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsOperationManager, ]
    serializer_class = ServiceRequestBaseSerializer

    def get_object(self):
        return get_object_or_404(ServiceRequest, id=self.kwargs.get('pk'))

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ServiceRequestBaseSerializer
        return ServiceRequestCreateSerializer


class StaffMemberListCreateView(ListCreateAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    # permission_classes = [IsOperationManager, ]
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = SupportStaffMember.objects.all()
        query_filter_params = {
            'staff_services__category__name__in': 'category',
            'work_address__zone__in': 'zone'
        }
        list_filter_dict = {'staff_services__category__name__in': {}, 'work_address__zone__in': {}}
        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request, list_filter_dict=list_filter_dict)
        queryset = queryset.filter(**extra_kwargs).distinct()
        return queryset

    def get_serializer_class(self):
            return SupportStaffMemberSerializer


class StaffMemberRetrieveUpdateView(RetrieveUpdateAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    # permission_classes = [IsOperationManager, ]
    pagination_class = StandardPagination

    def get_object(self):
        return get_object_or_404(SupportStaffMember, id=self.kwargs.get('pk'))

    def get_serializer_class(self):
        return SupportStaffMemberSerializer


class MultipleHouseDetailsToTenantSMSView(GenericAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsOperationManager, ]

    def post(self, request):
        phone_no = request.data['phone_no']
        name = request.data.get('name', '')
        houses_id_list = request.data.get('houses_id')
        house_ctr_content = []
        ctr = 1
        for j in houses_id_list:
            house_ctr_content.append("{ctr}.{url}".format(**{'ctr': ctr, 'url': get_house_url_from_house_id(j)}))
            ctr += 1
        content = HOUSE_LIST_DETAILS_MSG.format(**{'name': name, 'houses': '\n'.join(house_ctr_content)})
        MobileMessage.objects.create(content=content, phone_no=phone_no)
        return Response({STATUS: SUCCESS})


class PaymentsListView(ListCreateAPIView):
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsOperationManager, ]
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = TenantPayment.objects.all()
        query_filter_params = {
            'category__name__in': 'category',
            'status__in': 'status',
            'booking__space__house__address__zone__in': 'zone',
            'due_date__gte': 'from_date',
            'due_date__lte': 'to_date'
        }
        list_filter_dict = {'category__name__in': {}, 'status__in': {}, 'booking__space__house__address__zone__in': {}}
        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request, list_filter_dict=list_filter_dict)
        queryset = queryset.filter(**extra_kwargs).distinct()
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TenantPaymentSerializer
        else:
            return TenantPaymentBaseSerializer

    def create(self, request, *args, **kwargs):
        tenant = None
        if not request.data.get('tenant') and not request.data.get('booking'):
            return Response({STATUS: ERROR, 'message': 'one of booking or tenant is mandatory'},
                            status=status.HTTP_400_BAD_REQUEST)

        if 'booking' in request.data and request.data.get('booking', None):
            tenant = Booking.objects.get(id=request.data['booking']).tenant
        if 'tenant' in request.data and request.data.get('tenant'):
            tenant = get_object_or_404(Tenant, id=request.data['tenant'])
        if tenant:
            request.data['wallet'] = tenant.wallet.id
        return super(PaymentsListView, self).create(request, *args, **kwargs)


@authentication_classes([BasicAuthentication, TokenAuthentication])
@permission_classes([IsOperationManager, ])
@api_view(('GET',))
def search_view(request):
    search_term = request.query_params['q']
    search_type = request.query_params['type']
    search_by = request.query_params['by']

    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = None
    queryset = None
    serializer = None

    if search_type == 'tenant':
        queryset = Tenant.objects.all()
        if search_by == 'phone_no':
            queryset = queryset.filter(customer__phone_no__icontains=search_term)
        elif search_by == 'name':
            queryset = queryset.filter(customer__user__first_name__icontains=search_term)
        elif search_by == 'id':
            queryset = queryset.filter(id=search_term)

        result_page = paginator.paginate_queryset(queryset, request)
        serializer = TenantDetailSerializer(result_page, many=True, display_fields=['id', 'name', 'customer',
                                                                                    'permanent_address'])

    elif search_type == 'house':
        queryset = House.objects.all()
        if search_by == 'name':
            queryset = queryset.filter(name__icontains=search_term)
        elif search_by == 'id':
            queryset = queryset.filter(id=search_term)
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = HouseDetailSerializer(result_page, many=True, context={'request': request})

    else:
        raise Response(status=status.HTTP_404_NOT_FOUND)

    return paginator.get_paginated_response(serializer.data)


# TODO: Incomplete and buggy
class MetricDashboardAPIView(GenericAPIView):
    @staticmethod
    def get_user_metric_from_time_interval_array(array):
        result_array = []
        # TODO: Calculate and then replace random values by actual values
        for start_time, stop_time in array:
            result_array.append(
                {
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'active_users': random.randint(10, 100),
                    'inactive_users': random.randint(10, 100),
                    'churned_users': random.randint(10, 100),
                    'new_users': random.randint(10, 100),
                })

        return result_array

    @staticmethod
    def get_tenants_metric_from_time_interval_array(array):
        result_array = []
        active_tenants = Tenant.objects.filter(bookings__status=BOOKING_COMPLETE, bookings__moved_out=False)
        moved_out_tenants = Tenant.objects.filter(bookings__status=BOOKING_COMPLETE, bookings__moved_out=True)
        for start_time, stop_time in array:
            current_active_tenants = active_tenants.filter(bookings__license_start_date__gte=start_time,
                                                           bookings__license_start_date__lte=stop_time).distinct()
            current_moved_out_tenants = moved_out_tenants.filter(bookings__license_end_date__gte=start_time,
                                                                 bookings__license_end_date__lte=stop_time).distinct()

            result_array.append(
                {'start_time': start_time,
                 'stop_time': stop_time,
                 'active_tenants': current_active_tenants.count(),
                 'moved_out_tenants': current_moved_out_tenants.count()
                 })

        return result_array

    @staticmethod
    def get_revenue_metric_from_time_interval_array(array):
        result_array = []
        # TODO: Calculate and then replace random values by actual values
        for start_time, stop_time in array:
            result_array.append(
                {
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'revenue': random.randint(10000, 500000)
                })

        return result_array

    @staticmethod
    def get_payments_metric_from_time_interval_array(array):
        result_array = []
        # TODO: Calculate and then replace random values by actual values
        for start_time, stop_time in array:
            result_array.append(
                {
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'active_users': random.randint(10, 100),
                    'inactive_users': random.randint(10, 100),
                    'churned_users': random.randint(10, 100),
                    'new_users': random.randint(10, 100),
                })

        return result_array

    @staticmethod
    def get_activities_metric_from_time_interval_array(array):
        result_array = []
        # TODO: Calculate and then replace random values by actual values
        for start_time, stop_time in array:
            result_array.append(
                {
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'post_likes': random.randint(10, 100),
                    'comment_likes': random.randint(10, 100),
                    'posts_created': random.randint(10, 100),
                    'comments_created': random.randint(10, 100),
                    'messages_created': random.randint(10, 100)
                })

        return result_array

    @staticmethod
    def get_complaints_from_time_interval_array(array):
        result_array = []
        # TODO: Calculate and then replace random values by actual values
        for start_time, stop_time in array:
            result_array.append(
                {'start_time': start_time,
                 'stop_time': stop_time,
                 'unresolved_requests': random.randint(10, 100),
                 'resolved_requests': random.randint(10, 100)
                 })

        return result_array

    def get(self, request, *args, **kwargs):
        start_date, end_date = request.query_params.get('start_time'), request.query_params.get('end_time')
        date_a = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        # date_a = datetime.datetime(2018, 8, 9, 8, 24, 30, 993352)
        date_b = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        # date_b = datetime.datetime(2019, 8, 9, 7, 24, 30, 993352)
        total_time_interval = (date_b - date_a)
        delta_gap = total_time_interval / 10
        array = []
        for i in range(10):
            array.append((date_a + (i * delta_gap), date_a + ((i + 1) * delta_gap)))

        metric = request.query_params.get('metric')
        if metric == 'tenant':
            return Response({STATUS: SUCCESS, DATA: self.get_tenants_metric_from_time_interval_array(array)})
        elif metric == 'user':
            return Response({STATUS: SUCCESS, DATA: self.get_user_metric_from_time_interval_array(array)})
        elif metric == 'complaint':
            return Response({STATUS: SUCCESS, DATA: self.get_complaints_from_time_interval_array(array)})
        elif metric == 'activity':
            return Response({STATUS: SUCCESS, DATA: self.get_activities_metric_from_time_interval_array(array)})
        elif metric == 'payment':
            return Response({STATUS: SUCCESS, DATA: self.get_payments_metric_from_time_interval_array(array)})
        elif metric == 'revenue':
            return Response({STATUS: SUCCESS, DATA: self.get_revenue_metric_from_time_interval_array(array)})
        else:
            return Response({STATUS: ERROR, 'message': 'Incorrect Metric Provided'})
