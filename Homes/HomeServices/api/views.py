from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.generics import ListCreateAPIView, get_object_or_404, ListAPIView, RetrieveUpdateAPIView, \
    CreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from Homes.Bookings.utils import BOOKING_COMPLETE
from Homes.HomeServices.api.serializers import (ServiceRequestCreateUpdateSerializer, ServiceRequestSerializer,
                                                MajorServiceCategorySerializer, ServiceRequestImageSerializer)
from Homes.HomeServices.models import ServiceRequest, MajorServiceCategory
from Homes.Tenants.models import Tenant
from utility.pagination_utils import StandardPagination


class ServiceCategorySetPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class MajorServiceCategoryListView(ListAPIView):
    serializer_class = MajorServiceCategorySerializer
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = ServiceCategorySetPagination
    queryset = MajorServiceCategory.objects.all()


class ServiceRequestListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ServiceRequestSerializer
        else:
            return ServiceRequestCreateUpdateSerializer

    def get_queryset(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return ServiceRequest.objects.prefetch_related('booking__space', 'booking__tenant__customer') \
            .filter(booking__tenant=tenant)

    def create(self, request, *args, **kwargs):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        booking = tenant.bookings.filter(status=BOOKING_COMPLETE).last()
        if booking is None:
            return Response({'error': 'No active booking.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(booking=booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceRequestRetrieveUpdateView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ServiceRequestSerializer
        else:
            return ServiceRequestCreateUpdateSerializer

    def get_object(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return get_object_or_404(ServiceRequest.objects.prefetch_related('booking__space', 'booking__tenant__customer'),
                                 booking__tenant=tenant, pk=self.kwargs.get('pk'))


class ServiceRequestImageCreateView(CreateAPIView):
    serializer_class = ServiceRequestImageSerializer
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_request = None

    def create(self, request, *args, **kwargs):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        self.service_request = get_object_or_404(
            ServiceRequest.objects.prefetch_related('booking__space', 'booking__tenant__customer'),
            booking__tenant=tenant, pk=self.kwargs.get('pk'))

        return super(ServiceRequestImageCreateView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(service_request=self.service_request)
