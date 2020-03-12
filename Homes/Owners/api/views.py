from datetime import timedelta, datetime

import copy
from django.contrib.auth.models import User
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (ListAPIView, ListCreateAPIView, get_object_or_404, RetrieveUpdateDestroyAPIView)
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView, RetrieveDestroyAPIView, RetrieveAPIView, \
    RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Common.utils import CANCELLED, PAID
from Homes.Bookings.models import Booking, MonthlyRent
from Homes.Bookings.utils import BOOKING_COMPLETE
from Homes.Houses.api.serializers import HouseDetailSerializer, HouseCreateSerializer, HouseVisitSerializer, \
    HousePictureSerializer, SpaceSerializer, SpaceCreateSerializer
from Homes.Houses.api.views import perform_bed_update
from Homes.Owners.api.validators import validate_single_amount_or_ratio_value
from Homes.Houses.models import House, Bed, HouseVisit, HousePicture, Bill, Space, BillSplit
from Homes.Houses.utils import SHARED_ROOM, AVAILABLE, DISTRIBUTION_TYPE_AMOUNT, DISTRIBUTION_TYPE_RATIO
from Homes.Owners.api.serializers import OwnerSerializer, OwnerAddressDetailSerializer, OwnerDocumentSerializer, \
    OwnerHouseListSerializer, OwnerPaymentSerializer, OwnerNotificationListSerializer, \
    OwnerHouseExistingFacilitySerializer, \
    OwnerHouseBookingSerializer, OwnerWalletSerializer, OwnerListingSerializer, \
    WithdrawalRequestSerializer, TeamMemberCreateSerializer, VendorSerializer, VendorCreateSerializer, \
    BillCreateSerializer, TenantGroupCreateSerializer, BillSplitSerializer
from Homes.Owners.models import Owner, OwnerDocument, TeamMember, Vendor
from Homes.Owners.utils import OWNER_REFERRER_CASHBACK_AMOUNT, get_owner_month_start_time, get_rent_detail, \
    get_owner_month_end_time, LEAD_SOURCE_GUEST, LEAD_SOURCE_TENANT, LEAD_SOURCE_OWNER, LEAD_SOURCE_AFFILIATE
from Homes.Tenants.models import Tenant
from Homes.permissions import IsOwner
from Homes.utils import is_user_a_owner
from Notifications.models import Notification
from Notifications.utils import CASHBACK_NC
from UserBase.models import OTP
from utility.pagination_utils import StandardPagination
from utility.query_utils import get_filter_extra_kwargs
from utility.render_response_utils import STATUS, ERROR, SUCCESS, DATA
from utility.time_utils import get_datetime


class OwnerRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = OwnerSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        return get_object_or_404(Owner, user=self.request.user)


class OwnerCreateView(CreateAPIView):
    def create(self, request, *args, **kwargs):
        # check for all required fields
        required = ('phone_no', 'email', 'first_name', 'last_name', 'address', 'password', 'otp')
        if not all(request.data.get(field) for field in required):
            return Response({"error": "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)

        # validate otp
        otp = get_object_or_404(OTP, phone_no=request.data.get('phone_no'))
        if request.data.get('otp') != otp.password:
            return Response("Wrong OTP!", status=status.HTTP_400_BAD_REQUEST)

        # create username
        username = 'o{}'.format(request.data['phone_no'])

        # check for unique username and email
        if Owner.objects.filter(phone_no=request.data['phone_no']).exists():
            return Response({"error": "House owner with this phone number already exists!"},
                            status=status.HTTP_400_BAD_REQUEST)

        if Owner.objects.filter(user__email=request.data['email']).exists():
            return Response({"error": "House owner with this email already exists!"},
                            status=status.HTTP_400_BAD_REQUEST)

        # create new user
        user = User.objects.create_user(
            username=username,
            email=request.data.get('email'),
            password=request.data.get('password'),
            first_name=request.data.get('first_name'),
            last_name=request.data.get('last_name'),
        )
        user.save()

        # create new customer
        owner = Owner.objects.create(user=user, phone_no=request.data['phone_no'])

        # update owner address
        address_data = request.data['address']
        address_serializer = OwnerAddressDetailSerializer(owner.address, data=address_data, partial=True)
        if address_serializer.is_valid():
            address_serializer.update(owner.address, address_data)
        else:
            return Response(address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"key": token.key}, status=status.HTTP_201_CREATED)


class OwnerHouseListCreateView(ListCreateAPIView):
    permission_classes = [IsOwner, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def __init__(self, *args, **kwargs):
        super(OwnerHouseListCreateView, self).__init__(*args, **kwargs)
        self.owner = None

    def get_queryset(self):
        self.owner = get_object_or_404(Owner, user=self.request.user)
        params = self.request.query_params
        queryset = self.owner.houses.all()
        if params.get('managed_by', None) == 'Halanx':
            queryset = queryset.filter(managed_by=None, visible=True)

        if params.get('managed_by', None) == 'Me':
            queryset = queryset.filter(managed_by=self.owner)

        return queryset

    def create(self, request, *args, **kwargs):
        # check for all required fields
        required = ('name',)
        if not all(request.data.get(field) for field in required):
            return Response({"error": "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)
        self.owner = is_user_a_owner(request, raise_exception=True)
        return super(OwnerHouseListCreateView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.owner, managed_by=self.owner)

    def get_serializer_class(self):
        if self.request.method == "GET":
            from Homes.Houses.api.serializers import HouseListSerializer
            return HouseListSerializer
        else:
            from Homes.Houses.api.serializers import HouseCreateSerializer
            return HouseCreateSerializer


class OwnerHouseRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """
    get:
    Retrieve house detail by id
    """
    # serializer_class = HouseDetailSerializer
    permission_classes = (IsOwner,)
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    queryset = House.objects.all()

    def __init__(self, *args, **kwargs):
        super(OwnerHouseRetrieveUpdateDestroyView, self).__init__(*args, **kwargs)
        self.owner = None

    def get_object(self):
        house = get_object_or_404(House, id=self.kwargs.get("pk"))
        self.owner = is_user_a_owner(self.request, raise_exception=True)
        if house.managed_by is None and house.visible and house.owner == self.owner:  # if managed by Halanx
            return house

        elif house.managed_by == self.owner == house.owner:  # if user owns and manages the house
            return house

        # tenant = is_user_a_tenant(self.request, raise_exception=False)
        # if tenant:  # if user is a tenant and has booking with the space in the current house
        #     obj = get_object_or_404(Booking, tenant=tenant, space__in=house.spaces.all())
        #     from utility.logging_utils import cwlogger
        #     cwlogger.info(dict(type=self.__class__.__name__, tenant=tenant.id, house=self.kwargs.get('pk')))
        #     return obj
        raise Http404("Not found")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return HouseDetailSerializer
        else:
            return HouseCreateSerializer


class OwnerHousePictureListCreateView(ListCreateAPIView):
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    pagination_class = StandardPagination
    permission_classes = (IsOwner,)

    def __init__(self):
        super(OwnerHousePictureListCreateView, self).__init__()
        self.house = None

    def get_queryset(self):
        owner = is_user_a_owner(request=self.request, raise_exception=True)
        house = get_object_or_404(House, pk=self.kwargs.get('pk'), owner=owner)
        return HousePicture.objects.filter(house__owner=owner, house=house)

    def get_serializer_class(self):
        return HousePictureSerializer

    def create(self, request, *args, **kwargs):
        owner = is_user_a_owner(request=self.request, raise_exception=True)
        self.house = get_object_or_404(House, pk=self.kwargs.get('pk'), owner=owner)
        return super(OwnerHousePictureListCreateView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(house=self.house)


class OwnerHouseExistingFacilityListView(ListAPIView):
    serializer_class = OwnerHouseExistingFacilitySerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_queryset(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        house = get_object_or_404(House, owner=owner, pk=self.kwargs.get('pk'))
        return house.existing_facilities.all()


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def get_house_spaces_detail(request, pk):
    owner = get_object_or_404(Owner, user=request.user)
    house = get_object_or_404(House, pk=pk, owner=owner)

    spaces = house.spaces.filter(visible=True)
    space_types_metadata = spaces.values_list('type', 'subtype__name').distinct()
    space_types = {x[0]: [y[1] for y in space_types_metadata if y[0] == x[0]] for x in space_types_metadata}

    data = {}

    for space_type, space_subtypes in space_types.items():
        data[space_type] = {}
        for space_subtype in space_subtypes:
            subtype_spaces = spaces.filter(subtype__name=space_subtype)
            data[space_type][space_subtype] = {
                'occupied_count': subtype_spaces.exclude(availability=AVAILABLE).count(),
                'total_count': subtype_spaces.count(),
            }
            if space_type == SHARED_ROOM:
                data[space_type][space_subtype]['total_count'] = Bed.objects.filter(
                    room__space__in=subtype_spaces).count()
                data[space_type][space_subtype]['occupied_count'] = Bed.objects.filter(
                    room__space__in=subtype_spaces).exclude(availability=AVAILABLE).count()
    return Response(data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def get_house_rent_detail(request, pk):
    owner = get_object_or_404(Owner, user=request.user)
    house = get_object_or_404(House, pk=pk, owner=owner)

    start_time = get_owner_month_start_time()
    end_time = get_owner_month_end_time()

    collected_monthly_rents = MonthlyRent.objects.filter(status=PAID, payment__paid_on__gte=start_time,
                                                         booking__space__house=house,
                                                         booking__status=BOOKING_COMPLETE)

    expected_monthly_rents = MonthlyRent.objects.filter(payment__due_date__gte=start_time,
                                                        payment__due_date__lte=end_time,
                                                        booking__space__house=house,
                                                        booking__status=BOOKING_COMPLETE
                                                        ).exclude(status=CANCELLED)

    data = {
        'collected_rent_detail': get_rent_detail(collected_monthly_rents),
        'expected_rent_detail': get_rent_detail(expected_monthly_rents)
    }
    return Response(data)


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def get_house_tenants_detail(request, pk):
    owner = get_object_or_404(Owner, user=request.user)
    house = get_object_or_404(House, pk=pk, owner=owner)
    # ToDo even living this month
    bookings = Booking.objects.filter(space__house=house, status=BOOKING_COMPLETE, moved_out=False)

    data = {}

    for space_type, space_subtypes in house.space_types_dict.items():
        data[space_type] = {}
        for space_subtype in space_subtypes:
            subtype_bookings = bookings.filter(space__subtype__name=space_subtype)
            data[space_type][space_subtype] = OwnerHouseBookingSerializer(subtype_bookings, many=True).data

    return Response(data)


class OwnerWalletDetailView(RetrieveAPIView):
    serializer_class = OwnerWalletSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        return owner.wallet


class OwnerPaymentListView(ListAPIView):
    serializer_class = OwnerPaymentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_params(self):
        params = self.request.query_params
        start_date = params.get('start_time')
        end_date = params.get('end_date')
        payment_type = params.get('type')
        return start_date, end_date, payment_type

    def get_queryset(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        payments = owner.wallet.payments.filter(status=PAID)

        start_date, end_date, payment_type = self.get_params()
        if start_date:
            payments = payments.filter(paid_on__gte=get_datetime(start_date))
        if end_date:
            payments = payments.filter(paid_on__lte=get_datetime(end_date))
        if payment_type:
            payments = payments.filter(type=payment_type)
        return payments


class WithdrawalRequestListCreateView(ListCreateAPIView):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_queryset(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        return owner.withdrawal_requests.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        owner = get_object_or_404(Owner, user=self.request.user)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(owner=owner)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OwnerNotificationListView(ListAPIView):
    serializer_class = OwnerNotificationListSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_queryset(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        return owner.notifications.filter(display=True)


class OwnerDocumentListCreateView(ListCreateAPIView):
    serializer_class = OwnerDocumentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_queryset(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        return owner.documents.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        data = request.data
        data.pop('verified', None)
        owner = get_object_or_404(Owner, user=self.request.user)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(owner=owner)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        categories = ['Id', 'Employment', 'PAN', 'Electricity', 'Water', 'Maintenance', 'Insurance', 'Agreement',
                      'Others']
        data = {}
        for category in categories:
            data[category] = self.get_serializer(queryset.filter(type=category), many=True).data
        return Response(data)


class OwnerDocumentRetrieveDestroyView(RetrieveDestroyAPIView):
    serializer_class = OwnerDocumentSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        return get_object_or_404(OwnerDocument, owner=owner, pk=self.kwargs.get('pk'), is_deleted=False)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        document.is_deleted = True
        document.save()
        return Response({"detail": "Successfully deleted document."})


class OwnerReferAndEarnView(APIView):
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    # noinspection PyUnusedLocal
    @staticmethod
    def post(request, **kwargs):
        owner = get_object_or_404(Owner, user=request.user, referrer=None)
        referral_code = request.data.get('referral_code')
        tenant = get_object_or_404(Tenant, owner_referral_code=referral_code)
        owner.referrer = tenant
        owner.save()
        tenant.customer.hcash += OWNER_REFERRER_CASHBACK_AMOUNT
        tenant.customer.save()
        notification_payload = {'amount': OWNER_REFERRER_CASHBACK_AMOUNT}
        Notification(target=tenant.customer, category=CASHBACK_NC, payload=notification_payload).save(
            data={'amount': OWNER_REFERRER_CASHBACK_AMOUNT})
        return Response({'detail': 'Successfully availed cashback from owner refer & earn!'})


class OwnerListingCreateView(CreateAPIView):
    serializer_class = OwnerListingSerializer
    permission_classes = [AllowAny, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def create(self, request, *args, **kwargs):
        tenant = None
        owner = None
        source_category = None
        affiliate_code = None

        required_fields = ('name', 'phone_no')
        for required_field in required_fields:
            if required_field not in request.data:
                return Response({STATUS: ERROR, 'message': '{0} is mandatory'.format(required_field)},
                                status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            # Either Tenant or Owner
            tenant = Tenant.objects.filter(customer__user=request.user).first()
            owner = Owner.objects.filter(user=request.user).first()

            if tenant:
                source_category = LEAD_SOURCE_TENANT

            elif owner:
                source_category = LEAD_SOURCE_OWNER

            else:
                return Response({STATUS: ERROR, 'message': 'Unknown Authenticated User'},
                                status=status.HTTP_404_NOT_FOUND)

        if request.user.is_anonymous():
            if 'ref_id' in request.query_params:
                affiliate_code = request.query_params['ref_id']
                source_category = LEAD_SOURCE_AFFILIATE

            else:
                source_category = LEAD_SOURCE_GUEST

        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(referrer_tenant=tenant, referrer_owner=owner, affiliate_code=affiliate_code,
                            source_category=source_category)
            return Response({STATUS: SUCCESS, DATA: serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamMemberListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_queryset(self):
        return TeamMember.objects.filter(owner=is_user_a_owner(self.request, raise_exception=True))

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TeamMemberCreateSerializer
        else:
            return TeamMemberCreateSerializer

    def create(self, request, *args, **kwargs):
        owner = is_user_a_owner(request, raise_exception=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer=serializer, owner=owner)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, owner: Owner):
        serializer.save(owner=owner)

    def get_serializer_context(self):
        result = super(TeamMemberListCreateView, self).get_serializer_context()
        result['owner'] = is_user_a_owner(self.request, raise_exception=True)
        return result


class TeamMemberRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    def get_object(self):
        return get_object_or_404(TeamMember, pk=self.kwargs.get("pk"), owner=is_user_a_owner(self.request,
                                                                                             raise_exception=True))

    def get_serializer_class(self):
        return TeamMemberCreateSerializer

    def get_serializer_context(self):
        result = super(TeamMemberRetrieveUpdateDestroyView, self).get_serializer_context()
        result["owner"] = is_user_a_owner(self.request, raise_exception=True)
        return result


@api_view(['POST'])
def login_with_otp(request):
    """
    post:
    Generate token for user
    """
    phone_no = request.data.get('username')[1:]
    customer = get_object_or_404(Owner, phone_no=phone_no)
    user = customer.user
    otp = get_object_or_404(OTP, phone_no=phone_no, password=request.data.get('password'))
    if otp.timestamp >= timezone.now() - timedelta(minutes=10):
        token, created = Token.objects.get_or_create(user=user)
        return Response({"key": token.key}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)


class HouseVisitListView(ListAPIView):
    permission_classes = [IsOwner, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_queryset(self):
        owner = is_user_a_owner(self.request, raise_exception=True)

        query_filter_params = {
            'house_id': 'house',
            'visited': 'visited',
            'cancelled': 'cancelled'
        }

        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request)

        # To get upcoming visits and past visits
        if 'visit_type' in self.request.GET:
            if self.request.GET['visit_type'] == 'upcoming':
                extra_kwargs['scheduled_visit_time__gte'] = str(datetime.now())

            elif self.request.GET['visit_type'] == 'past':
                extra_kwargs['actual_visit_time__lte'] = str(datetime.now())

        return HouseVisit.objects.filter(house__owner=owner, **extra_kwargs)

    def get_serializer_class(self):
        return HouseVisitSerializer


class VendorListCreateView(ListCreateAPIView):
    pagination_class = StandardPagination
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsOwner, )

    def get_queryset(self):
        return Vendor.objects.filter(owner=is_user_a_owner(self.request, raise_exception=True))

    def get_serializer_class(self):
        if self.request.method == "GET":
            return VendorSerializer
        else:
            return VendorCreateSerializer

    def get_serializer_context(self):
        result = super(VendorListCreateView, self).get_serializer_context()
        result["owner"] = is_user_a_owner(self.request, raise_exception=True)
        return result


class VendorRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsOwner,)

    def __init__(self):
        super(VendorRetrieveUpdateDestroyView, self).__init__()
        self.owner = None

    def get_object(self):
        self.owner = is_user_a_owner(self.request, raise_exception=True)
        return get_object_or_404(Vendor, pk=self.kwargs.get("pk"), owner=self.owner)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return VendorCreateSerializer
        else:
            return VendorSerializer

    def get_serializer_context(self):
        result = super(VendorRetrieveUpdateDestroyView, self).get_serializer_context()
        result["owner"] = self.owner
        return result


def create_tenant_group(tenants_list_data, owner):
    tenant_group_serializer = TenantGroupCreateSerializer(data=tenants_list_data)
    tenant_group_serializer.is_valid(raise_exception=True)
    instance = tenant_group_serializer.save(owner=owner)
    return instance, tenant_group_serializer


@api_view(('POST',))
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsOwner,))
def create_tenant_group_view(request):
    owner = is_user_a_owner(request, raise_exception=True)
    instance, tenant_group_serializer = create_tenant_group(request.data.copy(), owner)
    return Response(tenant_group_serializer.data, status=status.HTTP_201_CREATED)


class BillListView(ListAPIView):
    serializer_class = BillCreateSerializer
    pagination_class = StandardPagination
    permission_classes = (IsOwner,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get_queryset(self):
        owner = is_user_a_owner(request=self.request, raise_exception=True)
        return Bill.objects.filter(owner=owner)


class HouseBillListCreateView(ListCreateAPIView):
    pagination_class = StandardPagination
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsOwner,)

    def __init__(self):
        super(HouseBillListCreateView, self).__init__()
        self.owner = None

    def create(self, request, *args, **kwargs):
        self.owner = is_user_a_owner(request, raise_exception=True)
        if 'tenants' in request.data:
            tenant_group, _ = create_tenant_group(request.data.copy(), self.owner)
            request.data['tenant_group'] = tenant_group.pk

        return super(HouseBillListCreateView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        house = get_object_or_404(House, owner=self.owner, pk=self.kwargs.get('pk'))
        serializer.save(owner=self.owner, house=house)

    def get_serializer_class(self):
        return BillCreateSerializer

    def get_queryset(self):
        self.owner = is_user_a_owner(request=self.request, raise_exception=True)
        query_filter_params = {
            'paid': 'paid',
            'due_date__lte': 'due_date__lte',
            'due_date__gte': 'due_date__gte',
            'amount__lte': 'amount__lte',
            'amount__gte': 'amount__gte'
        }

        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request)
        house = get_object_or_404(House, owner=self.owner, pk=self.kwargs.get('pk'))
        return Bill.objects.filter(owner=self.owner, house=house, **extra_kwargs)


class HouseSpaceListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def __init__(self):
        super(HouseSpaceListCreateView, self).__init__()
        self.owner = None

    def get_queryset(self):
        owner = is_user_a_owner(self.request, raise_exception=True)
        query_filter_params = {
            'type': 'type'
        }
        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request)
        return Space.objects.filter(house__owner=owner, **extra_kwargs)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SpaceSerializer
        elif self.request.method == "POST":
            return SpaceCreateSerializer

    def create(self, request, *args, **kwargs):
        required = ['house', 'type', 'subtype']
        if not all([request.data.get(field) for field in required]):
            return Response({"error": "Incomplete fields provided!"}, status=status.HTTP_400_BAD_REQUEST)

        self.owner = is_user_a_owner(self.request, raise_exception=True)
        house = get_object_or_404(House, id=request.data['house'], owner=self.owner)
        return super(HouseSpaceListCreateView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        dummy_instance = copy.deepcopy(instance)
        dummy_instance.pk = None
        space_name = instance.name
        # To create multiple spaces with same specifications
        instance_list = []
        no_of_clones = int(self.request.query_params.get('clone_count', 1))
        if no_of_clones == 1:
            instance_list.append(instance)
        else:
            instance_list = [copy.deepcopy(dummy_instance) for _ in range(no_of_clones)]
            ctr = 0
            for instance in instance_list:
                ctr += 1
                instance.name = space_name + str(ctr)
                instance.save()

        if self.request.data.get('bed_count', None):
                bed_count = int(self.request.data['bed_count'])
                for instance in instance_list:
                    perform_bed_update(space=instance, bed_count=bed_count)


class HouseSpaceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsOwner,)
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def __init__(self):
        super(HouseSpaceRetrieveUpdateDestroyView, self).__init__()
        self.owner = None
        self.shared_room_bed_count = None

    def get_object(self):
        self.owner = is_user_a_owner(self.request, raise_exception=True)
        space = get_object_or_404(Space, pk=self.kwargs.get("pk"), house__owner=self.owner)
        return space

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return SpaceCreateSerializer
        else:
            return SpaceSerializer

    def get_serializer_context(self):
        result = super(HouseSpaceRetrieveUpdateDestroyView, self).get_serializer_context()
        result["owner"] = self.owner
        return result

    def perform_update(self, serializer):
        instance = serializer.save()
        if self.request.data.get('bed_count', None):
            bed_count = int(self.request.data['bed_count'])
            perform_bed_update(space=instance, bed_count=bed_count)


@api_view(('POST',))
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsOwner,))
def create_bill_split(request, pk):
    """
        {
            'bill_split' :
            {
                'data_format' : {
                'distribution_type': 'amount',  # or 'ratio'
                'tenants': [
                    {
                        'id': 1,
                        'value': 1000 # or 0.4
                    },
                    {
                        'id': 2,
                        'value': 1500 # or 0.6
                    }
                ]
            }
        }
    """
    owner = is_user_a_owner(request, raise_exception=True)
    bill = get_object_or_404(Bill, pk=pk, owner=owner)

    data_format = request.data['bill_split']['data_format']

    value_sum = 0
    tenants = []
    for tenant in data_format['tenants']:
        try:
            obj = get_object_or_404(Tenant, pk=tenant['id'])
            tenants.append(obj)

            # Check if tenant has any booked space in owners house
            raise_exception = True
            try:
                if obj.current_booking.space.house.owner == owner:
                    raise_exception = False
            except Exception as E:
                print(E)
            finally:
                if raise_exception:
                    raise ValidationError({'detail': "This Tenant is not currently booked in any of your house space"})

            value_sum += validate_single_amount_or_ratio_value(bill=bill,
                                                               distribution_type=data_format['distribution_type'],
                                                               value=tenant['value'])

            if data_format['distribution_type'] == DISTRIBUTION_TYPE_AMOUNT:
                tenant['bill_contribution'] = tenant['value']
            elif data_format['distribution_type'] == DISTRIBUTION_TYPE_RATIO:
                tenant['bill_contribution'] = tenant['value'] * bill.amount
        except Http404:
            raise ValidationError({'detail': 'Not found'})

    if data_format['distribution_type'] == DISTRIBUTION_TYPE_AMOUNT:
        if value_sum != bill.amount:
            raise ValidationError({'detail': "Sum must be equal to {}".format(bill.amount)})

    elif data_format['distribution_type'] == DISTRIBUTION_TYPE_RATIO:
        if value_sum != 1:
            raise ValidationError({'detail': "Ratio Sum must be equal to 1"})

    bill_split_instance_list = []

    if len(set(tenants)) < len(tenants):
        raise ValidationError({'detail': "Duplicate Tenant Found"})

    if set(bill.tenant_group.tenants.all()) != set(tenants):
        raise ValidationError({'detail': 'Tenants Mismatched'})

    for tenant in data_format['tenants']:
        bill_split_instance = BillSplit.objects.create(tenant=Tenant.objects.get(pk=tenant['id']),
                                                       bill=bill,
                                                       amount=tenant['bill_contribution'],
                                                       due_date=bill.due_date)

        bill_split_instance_list.append(bill_split_instance)

    bill_split_serializer = BillSplitSerializer(bill_split_instance_list, many=True)
    return Response(bill_split_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def owner_exists(request, phone_no):
    """
    get:
    check if owner exists or not
    """
    if Owner.objects.filter(phone_no=phone_no).exists():
        return Response({"exists": "True"}, status=status.HTTP_200_OK)
    else:
        return Response({"exists": "False"}, status=status.HTTP_200_OK)
