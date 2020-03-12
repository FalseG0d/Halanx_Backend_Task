from django.db.models import Q, Min
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.generics import (RetrieveAPIView, ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView,
                                     get_object_or_404, UpdateAPIView)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from Homes.Houses.api.serializers import (HouseVisitSerializer, HouseDetailSerializer, HouseListSerializer,
                                          HouseVisitListSerializer, HouseApplicationSerializer,
                                          HouseVisitTimeSlotSerializer, SpaceSubTypeSerializer,
                                          HouseSearchSlugSerializer, PopularLocationSerializer, AmenitySerializer,
                                          OccupationSerializer,
                                          BillCategorySerializer)
from Homes.Houses.models import House, HouseVisit, HouseApplication, SpaceSubType, Occupation, BillCategory
from Homes.Houses.models import HouseSearchSlug, PopularLocation, \
    Amenity, SampleData
from Homes.Houses.utils import HOUSE_QUERY_DISTANCE_RANGE, SHARED_ROOM
from Homes.Owners.models import Owner
from Homes.Tenants.models import Tenant
from UserBase.models import Customer
from utility.pagination_utils import StandardPagination
from utility.query_utils import get_filter_extra_kwargs
from utility.time_utils import get_datetime


@api_view(['GET'])
def get_space_types(request):
    data = SpaceSubTypeSerializer(SpaceSubType.objects.all(), many=True).data
    return Response(data)


class HouseListView(ListAPIView):
    """
    get:
    List all houses (with filters)
    """
    serializer_class = HouseListSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination
    queryset = House.objects.all()

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            tenant = Tenant.objects.filter(customer__user=request.user).first()
        else:
            tenant = None
        if tenant:
            from utility.logging_utils import cwlogger
            cwlogger.info(dict(type=self.__class__.__name__, tenant=tenant.id, query=request.query_params))

        params = request.query_params
        latitude = params.get('latitude')
        longitude = params.get('longitude')
        radius = float(params.get('radius', HOUSE_QUERY_DISTANCE_RANGE))
        rent_max = params.get('rent_max')
        rent_min = params.get('rent_min')
        available_from = params.get('available_from')
        furnish_type = params.get('furnish_type')
        house_type = params.get('house_type')
        accomodation_types = params.get('accomodation_type')
        accomodation_allowed = params.get('accomodation_allowed')
        bhk_count = params.get('bhk_count')
        shared_room_bed_count = params.get('shared_room_bed_count')
        major_amenities = params.get('major_amenities')

        if tenant and not (latitude and longitude):
            latitude = tenant.customer.dlatitude
            longitude = tenant.customer.dlongitude

        if latitude and longitude:
            queryset = House.objects.nearby(latitude, longitude, radius)
        else:
            queryset = House.objects.filter(visible=True)

        if rent_max or rent_min:
            queryset = queryset.annotate(rent_start_from=Min("spaces__rent"))

        myquery = Q()

        if rent_max:
            myquery &= Q(rent_start_from__lte=int(rent_max))

        if rent_min:
            myquery &= Q(rent_start_from__gte=int(rent_min))

        if available_from:
            myquery &= Q(available_from__lte=get_datetime(available_from))

        if furnish_type:
            myquery &= Q(furnish_type__in=furnish_type.split(','))

        if house_type:
            myquery &= Q(house_type__in=house_type.split(','))

        if accomodation_types:
            subquery = Q()
            for accomodation_type in accomodation_types.split(','):
                subquery |= Q(available_accomodation_types__icontains=accomodation_type)
            myquery &= subquery

        if accomodation_allowed:
            subquery = Q()
            for accomodation_allowed_for in accomodation_allowed.split(','):
                subquery |= Q(accomodation_allowed__icontains=accomodation_allowed_for)
            myquery &= subquery

        if major_amenities:
            subquery = Q()
            for major_amenity in major_amenities.split(','):
                subquery |= (Q(amenities__amenity__name__icontains=major_amenity) & Q(amenities__amenity__is_major=True))
            myquery &= subquery

        if bhk_count:
            myquery &= Q(bhk_count=int(bhk_count))

        if shared_room_bed_count:
            myquery &= Q(spaces__shared_room__bed_count=int(shared_room_bed_count))

        queryset = queryset.filter(myquery)

        if latitude and longitude and len(queryset):
            houses = House.objects.sorted_nearby(latitude, longitude, radius, queryset)
            house_distance_map = {house.id: distance for house, distance in houses}
            page = self.paginate_queryset(list(zip(*houses))[0])
            data = self.get_serializer(page, many=True).data
            data = [{'distance': round(house_distance_map[row['id']], 1), **row} for idx, row in enumerate(data)]
        else:
            page = self.paginate_queryset(queryset)
            data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)


class HouseRetrieveView(RetrieveAPIView):
    """
    get:
    Retrieve house detail by id
    """
    serializer_class = HouseDetailSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    queryset = House.objects.filter(visible=True)

    def get_object(self):
        if self.request.user.is_authenticated:
            tenant = Tenant.objects.filter(customer__user=self.request.user).first()
        else:
            tenant = None
        if tenant:
            from utility.logging_utils import cwlogger
            cwlogger.info(dict(type=self.__class__.__name__, tenant=tenant.id, house=self.kwargs.get('pk')))
        return super(HouseRetrieveView, self).get_object()


class HouseVisitTimeSlotView(RetrieveAPIView):
    """
    get:
    List free time slots for house visit
    """
    serializer_class = HouseVisitTimeSlotSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    queryset = House.objects.filter(visible=True)


class HouseVisitListCreateView(ListCreateAPIView):
    """
    get:
    List house visits of customer
    @query_param visited : (true/false)

    post:
    Create a new house visit of customer
    """
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return HouseVisitListSerializer
        else:
            return HouseVisitSerializer

    def get_queryset(self):
        customer = get_object_or_404(Customer, user=self.request.user)
        visits = customer.house_visits.filter(cancelled=False)

        visited = self.request.GET.get('visited')

        query_filter_params = {
            'house_id': 'house'
        }
        extra_kwargs = get_filter_extra_kwargs(query_filter_params, self.request)

        if visited == 'true':
            return visits.filter(visited=True, **extra_kwargs).order_by('-scheduled_visit_time')
        elif visited == 'false':
            return visits.filter(visited=False, **extra_kwargs).order_by('cancelled', '-scheduled_visit_time')
        else:
            return visits.filter(**extra_kwargs)

    def create(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer, user=request.user)
        house = get_object_or_404(House, pk=request.data.get('house'))
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=customer, area_manager=house.area_managers.first())

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HouseVisitRetrieveUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    """
    get:
    Retrieve house visit by id

    patch:
    Update house visit by id

    delete:
    Cancel house visit by id
    """
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return HouseVisitListSerializer
        else:
            return HouseVisitSerializer

    def get_object(self):
        customer = get_object_or_404(Customer, user=self.request.user)
        return get_object_or_404(HouseVisit, pk=self.kwargs.get('pk'), customer=customer, cancelled=False)

    def destroy(self, request, *args, **kwargs):
        house_visit = self.get_object()
        house_visit.cancelled = True
        house_visit.save()
        return Response({"detail": "Successfully cancelled the visit."}, status=status.HTTP_200_OK)


class HouseApplicationCreateView(ListCreateAPIView):
    """
    post:
    Create house application
    """
    serializer_class = HouseApplicationSerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    queryset = HouseApplication.objects.all()

    def create(self, request, *args, **kwargs):
        owner = get_object_or_404(Owner, user=request.user)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=owner)
            return Response({"detail": "Application created successfully!"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TenantFavoritePlaceToggleView(UpdateAPIView):
    """
    patch:
    Favorite a house
    """
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def update(self, request, *args, **kwargs):
        tenant = get_object_or_404(Tenant, customer__user=request.user)
        house = get_object_or_404(House, pk=self.kwargs.get('pk'))

        if house not in tenant.favorite_houses.all():
            tenant.favorite_houses.add(house)
            return Response({"result": "favorited"}, status=status.HTTP_200_OK)
        else:
            tenant.favorite_houses.remove(house)
            return Response({"result": "unfavorited"}, status=status.HTTP_200_OK)


@api_view(['GET'])
def share_house(request, pk):
    """
    house share
    """
    house = get_object_or_404(House, pk=pk, visible=True)
    return Response({'title': "{} {} in {}, {}".format(house.name, house.house_type, house.address.city,
                                                       house.address.state),
                     'description': house.description,
                     'image': house.cover_pic_url}, status=status.HTTP_200_OK)


class HouseSearchSlugRetrieveView(RetrieveAPIView):
    serializer_class = HouseSearchSlugSerializer
    queryset = HouseSearchSlug.objects.all()

    def get_object(self):
        slug_obj = get_object_or_404(HouseSearchSlug, slug=self.kwargs.get('slug'))
        # noinspection PyAttributeOutsideInit
        self.fields = slug_obj.fields
        return slug_obj

    def get_serializer_context(self):
        data = super(HouseSearchSlugRetrieveView, self).get_serializer_context()
        data['fields'] = self.fields
        return data


class PopularLocationListView(ListAPIView):
    queryset = PopularLocation.objects.all()
    serializer_class = PopularLocationSerializer


class AmenityListView(ListAPIView):
    serializer_class = AmenitySerializer

    def get_queryset(self):
        params = self.request.query_params
        queryset = Amenity.objects.all()
        is_major = params.get('is_major')

        if is_major == 'true':
            queryset = queryset.filter(is_major=True)

        elif is_major == 'false':
            queryset = queryset.filter(is_major=False)

        return queryset


@api_view(('GET', 'POST', 'PATCH', 'DELETE'))
def save_request_data(request):
    query_params = request.query_params
    body_data = request.data

    SampleData.objects.create(query_params=str(query_params), body_data=str(body_data))
    return Response('Ok')


def perform_bed_update(space, bed_count):
    if space.type == SHARED_ROOM:
        space.shared_room.bed_count = bed_count
        space.shared_room.save()
        space.save()


class OccupationListView(ListAPIView):
    """
    These occupations are used in Owner App for vendors
    """
    serializer_class = OccupationSerializer

    def get_queryset(self):
        return Occupation.objects.all()


class BillCategoryListView(ListAPIView):
    queryset = BillCategory.objects.all()
    serializer_class = BillCategorySerializer
    pagination_class = StandardPagination
