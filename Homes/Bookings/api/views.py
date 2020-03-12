import logging
from functools import partial

from django.http import HttpResponse
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView, ListCreateAPIView, get_object_or_404, RetrieveUpdateAPIView, \
    ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from Homes.Bookings.api.serializers import BookingListSerializer, BookingDetailSerializer, \
    AdvanceBookingDetailSerializer, AdvanceBookingCreateSerializer, \
    BookingFacilityUpdateQuantityAcknowledgementAtMoveInSerializer, BookingMoveInDigitalSignatureSerializer
from Homes.Bookings.models import Booking, AdvanceBooking, BookingFacility, BookingMoveInDigitalSignature
from Homes.Bookings.utils import BOOKING_PARTIAL, BOOKING_CANCELLED, BOOKING_COMPLETE, load_rent_agreement, \
    load_rent_agreement_as_html, AGREEMENT_SIGN_VERIFICATION_ONGOING
from Homes.Houses.models import Space, SpaceSubType
from Homes.Houses.utils import AVAILABLE
from Homes.Tenants.models import Tenant
from MobileMessage.models import MobileMessage
from Promotions.models import PromoCode, PromoCodeUser
from Promotions.utils import PROMOCODE_INVALID_MSG, RENT_DISCOUNT_PROMOCODE, PROMOCODE_UNUSED
from UserBase.models import Customer
from utility.pagination_utils import StandardPagination
from utility.render_response_utils import STATUS, ERROR, SUCCESS
from utility.time_utils import get_datetime

logger = logging.getLogger(__name__)


class BookingListCreateView(ListCreateAPIView):
    """
    get:
    List all bookings of tenant

    post:
    Create new booking
    """
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BookingListSerializer
        else:
            return BookingDetailSerializer

    def get_queryset(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return tenant.bookings.all()

    def create(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer, user=self.request.user)
        tenant = get_object_or_404(Tenant, customer=customer)
        space = get_object_or_404(Space, id=request.data.get('space'), availability=AVAILABLE, visible=True)
        license_start_date = request.data.get('license_start_date')
        # try:
        #     booking, _ = Booking.objects.get_or_create(tenant=tenant, space=space, license_start_date=license_start_date)
        # except Booking.MultipleObjectsReturned:
        booking = Booking.objects.create(tenant=tenant, space=space, license_start_date=license_start_date)

        serializer = self.get_serializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CurrentBookingRetrieveView(RetrieveAPIView):
    """
    get:
    Retrieve current partial/complete booking of user
    """
    serializer_class = BookingDetailSerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return tenant.current_booking


class BookingDetailView(RetrieveUpdateAPIView):
    """
    get:
    Retrieve booking by id

    patch:
    Update booking by id
    - Cancel a partial booking
    - Set license end date
    - Update lock-in period
    - Add promo-code
    """
    serializer_class = BookingDetailSerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_object(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        booking = get_object_or_404(Booking, tenant=tenant, pk=self.kwargs.get('pk'))
        return booking

    def update(self, request, *args, **kwargs):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        booking = get_object_or_404(Booking, tenant=tenant, pk=self.kwargs.get('pk'))

        messages = []

        if booking.status == BOOKING_PARTIAL:

            # cancel booking
            booking_status = request.data.get('status')
            if booking_status == BOOKING_CANCELLED:
                booking.status = booking_status
                booking.save()
                messages.append("Successfully cancelled the booking.")

            # set booking lock-in period
            lock_in_period = request.data.get('lock_in_period')
            if lock_in_period:
                booking.lock_in_period = int(lock_in_period)
                booking.save()
                messages.append("Successfully updated the lock-in period.")

            # add promo-code
            promo_code_str = request.data.get('promo_code')
            if promo_code_str and not booking.promo_code:
                promo_code = get_object_or_404(PromoCode, code=promo_code_str, type=RENT_DISCOUNT_PROMOCODE)
                is_valid, msg = promo_code.can_redeem(tenant.customer)
                if is_valid:
                    booking.promo_code = promo_code
                    booking.rent = max(booking.rent - promo_code.value, 0)
                    booking.security_deposit = booking.rent * booking.security_deposit_by_months
                    booking.save()
                    PromoCodeUser.objects.create(customer=tenant.customer, promo_code=promo_code)
                    messages.append("Successfully applied the promo code!")
                else:
                    messages.append(msg)

        elif booking.status == BOOKING_COMPLETE:

            # set booking license end date
            booking_license_end_date = get_datetime(request.data.get('license_end_date'))
            booking.license_end_date = booking_license_end_date
            booking.save()
            messages.append("Successfully updated the license end date!")

        serializer = self.get_serializer(booking)
        data = {'messages': messages, **serializer.data}
        return Response(data)


class AdvanceBookingListCreateView(ListCreateAPIView):
    queryset = AdvanceBooking.objects.all()
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'GET':
            return AdvanceBookingDetailSerializer(*args, **kwargs)
        else:
            return AdvanceBookingCreateSerializer(*args, **kwargs)

    def get_queryset(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return tenant.advance_bookings.filter(cancelled=False)

    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        try:
            space_type = SpaceSubType.objects.get(pk=int(data.get('space_subtype'))).parent_type
        except Exception as e:
            logger.debug(data)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if data.get('promo_code'):
            promo_code = PromoCode.objects.filter(code=data['promo_code']).first()
            if promo_code and AdvanceBooking.objects.filter(tenant=tenant).exclude(promo_code=None).count() is 0:
                is_valid, msg = promo_code.can_redeem(tenant.customer)
                if is_valid:
                    PromoCodeUser.objects.create(customer=tenant.customer, promo_code=promo_code)
                    data['promo_code'] = promo_code.pk
            else:
                data.pop('promo_code')

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(tenant=tenant, space_type=space_type)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.debug(data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteBookingsListView(ListAPIView):
    serializer_class = BookingDetailSerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def get_queryset(self):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        return tenant.bookings.select_related('space',
                                              'space__house',
                                              'space__house__address').filter(status=BOOKING_COMPLETE,
                                                                              moved_out=False).order_by('-id')


class MoveInBookingFacilityQuantityAcknowledgementAPIView(UpdateAPIView):
    """
    API to updated the quantities_acknoeldged when verifying asset while move in
    """
    queryset = BookingFacility.objects.all()
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [BasicAuthentication, TokenAuthentication]

    def patch(self, request, *args, **kwargs):
        tenant = get_object_or_404(Tenant, customer__user=self.request.user)
        facilities_data = request.data['data']

        facility_mismatch_items = []

        if tenant.current_booking:
            booking_facilities = tenant.current_booking.facilities.all()

            for facility_data in facilities_data:
                facility = booking_facilities.get(id=facility_data['id'])
                facility.quantity_acknowledged = int(facility_data['quantity_acknowledged'])
                facility.save()

                if facility.quantity_acknowledged != facility.quantity:
                    facility_mismatch_items.append(facility.item.name)

            # Send a message if Quantity of booking Facility Does Not Match
            if facility_mismatch_items:
                mismatch_items = ', '.join(facility_mismatch_items)
                MobileMessage(phone_no='9773852058',
                              content='Facilities Quantity Mismatched for items:' + mismatch_items +
                                      "for booking id : " + str(tenant.current_booking.id)).save()

            return Response({STATUS: SUCCESS})

        else:
            return Response({STATUS: ERROR, 'message': 'You have to book your space first'},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(('GET',))
@permission_classes((IsAuthenticated, ))
def rent_agreement_for_current_booking_view(request):
    tenant = get_object_or_404(Tenant, customer__user=request.user)
    booking = tenant.current_booking
    agreement_format = request.query_params.get('agreement_format', 'pdf')
    if agreement_format == 'html':
        return HttpResponse(load_rent_agreement_as_html(booking))
    else:
        return HttpResponse(load_rent_agreement(booking), content_type='application/pdf')


class BookingMoveInDigitalSignatureUploadView(CreateAPIView):
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    def __init__(self):
        super(BookingMoveInDigitalSignatureUploadView, self).__init__()
        self.booking = None

    def create(self, request, *args, **kwargs):
        tenant = get_object_or_404(Tenant, customer__user=request.user)
        booking = tenant.current_booking
        if booking:
            self.booking = booking
        else:
            return Response({STATUS: ERROR, 'message': 'You must have to book some space first'},
                            status=status.HTTP_400_BAD_REQUEST)

        return super(BookingMoveInDigitalSignatureUploadView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(booking=self.booking)
        self.booking.agreement_signed = True
        self.booking.agreement_verification_status = AGREEMENT_SIGN_VERIFICATION_ONGOING
        self.booking.save()

    def get_serializer_class(self):
        if self.booking:
            try:
                signature = self.booking.signature
                serializer_class = partial(BookingMoveInDigitalSignatureSerializer, instance=signature, partial=True)

            except BookingMoveInDigitalSignature.DoesNotExist:
                serializer_class = BookingMoveInDigitalSignatureSerializer

            return serializer_class
