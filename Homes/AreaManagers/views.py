from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import AnonymousUser
from django.forms import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.generics import get_object_or_404

from Common.utils import PENDING, DEPOSIT, CANCELLED, PAID
from Homes.AreaManagers.forms import SpaceUpdateForm
from Homes.AreaManagers.models import AreaManager
from Homes.Bookings.models import FacilityItem, Booking, BookingFacility, ExistingTenantOnboarding, MonthlyRent
from Homes.Bookings.utils import SUB_UNIT_ITEM, COMMON_AREA_ITEM, load_rent_agreement, EXISTING_TENANT_BOOKING, \
    BOOKING_COMPLETE, ONBOARDING_CHARGES, TOKEN_AMOUNT
from Homes.Houses.models import HouseVisit, House, SpaceSubType, Space
from Homes.Houses.utils import HouseAccomodationTypeCategories, SHARED_ROOM, PRIVATE_ROOM, FLAT, AVAILABLE
from Homes.Tenants.models import Tenant, TenantPayment, TenantDocument
from Homes.Tenants.utils import get_tenant_profile_completion
from Transaction.models import CustomerTransaction
from UserBase.models import Picture
from utility.customer_utils import create_customer
from utility.online_transaction_utils import CASH
from utility.sms_utils import send_sms
from utility.time_utils import get_datetime
from django.forms.formsets import formset_factory

LOGIN_URL = '/homes/manage/login/'


def is_area_manager(user):
    return AreaManager.objects.filter(user=user).count()


area_manager_login_test = user_passes_test(is_area_manager, login_url=LOGIN_URL)


def area_manager_login_required(view):
    decorated_view = login_required(area_manager_login_test(view), login_url=LOGIN_URL)
    return decorated_view


def logout_view(request):
    logout(request)
    request.session.flush()
    request.user = AnonymousUser
    return HttpResponseRedirect(reverse(home_page))


def login_view(request):
    error_msg = None
    logout(request)
    if request.POST:
        username, password = request.POST['username'], request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if is_area_manager(user):
                if user.is_active:
                    login(request, user)
                    next_page = request.GET.get('next')
                    if next_page:
                        return HttpResponseRedirect(next_page)
                    else:
                        return HttpResponseRedirect(reverse(home_page))
            else:
                error_msg = 'You are not an Area Manager.'
        else:
            error_msg = 'Username and Password do not match.'
    return render(request, 'login_form.html', {'error': error_msg})


@area_manager_login_required
@require_http_methods(['GET'])
def home_page(request):
    return render(request, 'home_page.html')


@area_manager_login_required
@require_http_methods(['GET', 'POST'])
def tenants_page(request):
    if request.method == 'GET':
        return render(request, 'tenants/tenant_page.html')

    if request.method == 'POST':
        phone_no = request.POST.get('phone_no')
        try:
            tenant = Tenant.objects.select_related('customer', 'customer__user',
                                                   'permanent_address').get(customer__phone_no=phone_no)
            tenant_profile_missing_fields, tenant_profile_completion_percentage = get_tenant_profile_completion(tenant)
        except Tenant.DoesNotExist:
            return render(request, 'tenants/tenant_page.html',
                          {'msg': 'Tenant with phone no. {} not found.'.format(phone_no),
                           'err': 'tenant_not_found', 'phone_no': phone_no})

        return render(request, 'tenants/tenant_page.html', {'tenant': tenant,
                                                            'tenant_profile_completion_percentage':
                                                                tenant_profile_completion_percentage,
                                                            'tenant_profile_missing_fields':
                                                                tenant_profile_missing_fields})


@area_manager_login_required
@require_http_methods(['GET', 'POST'])
def create_new_tenant_view(request):
    if request.method == 'GET':
        return render(request, 'tenants/new_tenant_form.html')

    if request.method == 'POST':
        data = request.POST
        tenant = Tenant.objects.filter(customer__phone_no=data.get('phone_no')).first()
        if tenant:
            return JsonResponse({'detail': "Customer already exists!"})
        create_customer(data.get('first_name'), data.get('last_name'), data.get('phone_no'))
        return JsonResponse({'detail': "Customer created successfully!"})


@area_manager_login_required
@require_http_methods(['GET', 'POST'])
def tenant_profile_edit_view(request, pk):
    try:
        tenant = Tenant.objects.select_related('customer', 'customer__user', 'permanent_address',
                                               'company_address', 'bank_detail').get(pk=pk)
        if tenant.documents.count():
            document = tenant.documents.last().image.url
        else:
            document = None
    except Tenant.DoesNotExist:
        return render(request, 'tenants/tenant_edit_form.html', {'msg': 'Tenant not found.'})

    if request.method == 'GET':
        return render(request, 'tenants/tenant_edit_form.html', {'tenant': tenant, 'document': document})

    if request.method == 'POST':
        if request.GET.get('type') == 'media':
            if request.FILES.get('profile_pic'):
                Picture.objects.create(customer=tenant.customer, image=request.FILES['profile_pic'],
                                       is_profile_pic=True)
            if request.FILES.get('document'):
                TenantDocument.objects.create(tenant=tenant, image=request.FILES['document'], type='Id',
                                              verified=True)
            return render(request, 'tenants/tenant_edit_form.html', {'tenant': tenant, 'document': document})

        data = dict(request.POST)

        # convert 'None' to None
        for key, val in data.items():
            if val == ['None']:
                data[key] = None
            else:
                data[key] = val[0]

        tenant.customer.user.first_name = data.get('first_name')
        tenant.customer.user.last_name = data.get('last_name')
        tenant.customer.user.email = data.get('email')
        tenant.customer.user.save()

        tenant.customer.dob = get_datetime(data.get('dob'))
        tenant.customer.save()

        tenant.parent_name = data.get('parent_name')
        tenant.parent_phone_no = data.get('parent_phone_no')
        tenant.emergency_contact_name = data.get('emergency_contact_name')
        tenant.emergency_contact_relation = data.get('emergency_contact_relation')
        tenant.emergency_contact_phone_no = data.get('emergency_contact_phone_no')
        tenant.emergency_contact_email = data.get('emergency_contact_email')
        tenant.job_position = data.get('job_position')
        tenant.company_name = data.get('company_name')
        tenant.company_phone_no = data.get('company_phone_no')
        tenant.company_email = data.get('company_email')
        tenant.company_joining_date = get_datetime(data.get('company_joining_date'))
        tenant.company_leaving_date = get_datetime(data.get('company_leaving_date'))
        tenant.save()

        tenant.permanent_address.street_address = data.get('permanent_street_address')
        tenant.permanent_address.city = data.get('permanent_city')
        tenant.permanent_address.state = data.get('permanent_state')
        tenant.permanent_address.pincode = data.get('permanent_pincode')
        tenant.permanent_address.country = data.get('permanent_country')
        tenant.permanent_address.save()

        tenant.company_address.street_address = data.get('company_street_address')
        tenant.company_address.city = data.get('company_city')
        tenant.company_address.state = data.get('company_state')
        tenant.company_address.pincode = data.get('company_pincode')
        tenant.company_address.country = data.get('company_country')
        tenant.company_address.save()
        tenant.company_address.save()

        tenant.bank_detail.account_holder_name = data.get('account_holder_name')
        tenant.bank_detail.account_number = data.get('account_number')
        tenant.bank_detail.account_type = data.get('account_type')
        tenant.bank_detail.bank_name = data.get('bank_name')
        tenant.bank_detail.bank_branch = data.get('bank_branch')
        tenant.bank_detail.bank_branch_address = data.get('bank_branch_address')
        tenant.bank_detail.ifsc_code = data.get('ifsc_code')
        tenant.bank_detail.save()

        return JsonResponse({'detail': 'done'})


@area_manager_login_required
@require_http_methods(['GET'])
def tenant_bookings_page(request, pk):
    try:
        tenant = Tenant.objects.select_related('customer', 'customer__user', 'permanent_address').get(pk=pk)
    except Tenant.DoesNotExist:
        return render(request, 'tenants/tenant_bookings_page.html', {'msg': 'Tenant not found.'})
    bookings = Booking.objects.select_related('space', 'space__house', 'space__house__address',
                                              'space__subtype').filter(tenant=tenant).order_by('-id')
    if not bookings.count():
        return render(request, 'tenants/tenant_bookings_page.html', {'msg': 'No booking found.'})
    return render(request, 'tenants/tenant_bookings_page.html', {'tenant': tenant, 'bookings': bookings})


@area_manager_login_required
@require_http_methods(['GET'])
def tenant_payments_page(request, pk):
    try:
        tenant = Tenant.objects.select_related('customer', 'customer__user', 'permanent_address').get(pk=pk)
    except Tenant.DoesNotExist:
        return render(request, 'tenants/tenant_payments_page.html', {'msg': 'Tenant not found.'})

    if request.GET.get('booking'):
        booking = Booking.objects.filter(id=int(request.GET.get('booking'))).first()
    else:
        booking = tenant.current_booking
    if not booking:
        return render(request, 'tenants/tenant_payments_page.html', {'msg': 'No booking found.'})
    payments = (TenantPayment.objects.select_related('category', 'transaction')
        .filter(wallet__tenant=tenant, booking=booking)
        .exclude(status=CANCELLED))[::-1]
    return render(request, 'tenants/tenant_payments_page.html', {'tenant': tenant, 'payments': payments})


# Area manager can Change status of any payment and can create CustomerTransaction
@area_manager_login_required
@require_http_methods(['POST'])
def tenant_payment_edit_view(request, pk):
    try:
        payment = TenantPayment.objects.get(pk=pk)
    except TenantPayment.DoesNotExist:
        return JsonResponse({"detail": "Wrong Payment Id."})

    data = request.POST
    payment.status = data['status']
    payment.amount = data['amount']
    payment.paid_on = get_datetime(data['paid_on']) if data['paid_on'] != 'None' else None
    payment.save()

    if payment.status == PAID:
        if not payment.transaction:
            payment.transaction = CustomerTransaction.objects.create(customer=payment.wallet.tenant.customer,
                                                                     amount=payment.amount)
            payment.save()
        else:
            payment.transaction.amount = payment.amount
        payment.transaction.transaction_id = data['transaction_id'] if data['transaction_id'] != 'None' else None
        payment.transaction.payment_gateway = data['payment_gateway'] if data['payment_gateway'] != 'None' else None
        payment.transaction.complete = True
        payment.transaction.save()

    return JsonResponse({"detail": "Done!"})


@area_manager_login_required
@require_http_methods(['GET'])
def move_in_page(request, pk):
    try:
        tenant = Tenant.objects.select_related('customer', 'customer__user', 'permanent_address').get(pk=pk)
    except Tenant.DoesNotExist:
        return render(request, 'bookings/move_in_form.html', {'msg': 'Tenant not found.'})

    if request.GET.get('booking'):
        booking = Booking.objects.select_related('space', 'space__house', 'space__house__address'
                                                 ).filter(id=int(request.GET.get('booking'))).first()
    else:
        booking = tenant.current_booking
    if not booking:
        return render(request, 'bookings/move_in_form.html', {'msg': 'No booking found.'})

    sub_unit_facility_items = FacilityItem.objects.filter(type=SUB_UNIT_ITEM)
    sub_unit_facilities = booking.facilities.select_related('item').filter(item__type=SUB_UNIT_ITEM)
    common_area_facility_items = FacilityItem.objects.filter(type=COMMON_AREA_ITEM)
    common_area_facilities = booking.facilities.select_related('item').filter(item__type=COMMON_AREA_ITEM)

    return render(request, 'bookings/move_in_form.html', {'tenant': tenant, 'booking': booking, 'space': booking.space,
                                                          'house': booking.space.house,
                                                          'sub_unit_facilities': sub_unit_facilities,
                                                          'sub_unit_facility_items': sub_unit_facility_items,
                                                          'common_area_facilities': common_area_facilities,
                                                          'common_area_facility_items': common_area_facility_items,
                                                          })


@area_manager_login_required
@require_http_methods(['POST'])
def move_in_confirmation_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    items = list(map(int, request.POST.getlist('item')))
    quantities = list(map(int, request.POST.getlist('quantity')))
    remarks = request.POST.getlist('remark')
    data = list(zip(items, quantities, remarks))
    booking.facilities.exclude(item__id__in=items).delete()

    for row in data:
        if not booking.facilities.filter(item__id=row[0]).count():
            item = FacilityItem.objects.get(id=row[0])
            booking.facilities.add(BookingFacility.objects.create(item=item, quantity=row[1], remark=row[2]))

    booking.move_in_notes = request.POST.get('notes')
    booking.save()
    return JsonResponse({'detail': 'Successfully saved the booking details!'})


@area_manager_login_required
@require_http_methods(['GET'])
def move_in_agreement_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    return HttpResponse(load_rent_agreement(booking), content_type='application/pdf')


@area_manager_login_required
@require_http_methods(['GET'])
def move_out_page(request, pk):
    try:
        tenant = Tenant.objects.select_related('customer', 'customer__user', 'permanent_address').get(pk=pk)
    except Tenant.DoesNotExist:
        return render(request, 'bookings/move_out_form.html', {'msg': 'Tenant not found.'})

    if request.GET.get('booking'):
        booking = Booking.objects.select_related('space', 'space__house', 'space__house__address'
                                                 ).filter(id=int(request.GET.get('booking'))).first()
    else:
        booking = tenant.current_booking
    if not booking:
        return render(request, 'bookings/move_out_form.html', {'msg': 'No booking found.'})

    sub_unit_facility_items = FacilityItem.objects.filter(type=SUB_UNIT_ITEM)
    sub_unit_facilities = booking.facilities.select_related('item').filter(item__type=SUB_UNIT_ITEM)
    common_area_facility_items = FacilityItem.objects.filter(type=COMMON_AREA_ITEM)
    common_area_facilities = booking.facilities.select_related('item').filter(item__type=COMMON_AREA_ITEM)

    pending_payments = TenantPayment.objects.filter(booking=booking, status=PENDING, type=DEPOSIT)

    return render(request, 'bookings/move_out_form.html', {'tenant': tenant, 'booking': booking, 'space': booking.space,
                                                           'house': booking.space.house,
                                                           'sub_unit_facilities': sub_unit_facilities,
                                                           'sub_unit_facility_items': sub_unit_facility_items,
                                                           'common_area_facilities': common_area_facilities,
                                                           'common_area_facility_items': common_area_facility_items,
                                                           'payments': pending_payments})


@area_manager_login_required
@require_http_methods(['POST'])
def move_out_confirmation_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    booking.moved_out = True
    booking.area_manager_notes = request.POST.get('area_manager_notes')
    booking.save()

    statuses = request.POST.getlist('status')
    remarks = request.POST.getlist('remark')
    facility_ids = list(map(int, request.POST.getlist('item')))
    facilities = BookingFacility.objects.filter(id__in=facility_ids)
    for idx, facility in enumerate(facilities):
        facility.status = statuses[idx]
        facility.remark = remarks[idx]
        facility.save()
    return JsonResponse({'detail': 'done'})


@area_manager_login_required
@require_http_methods(['GET'])
def onboard_page(request, pk):
    try:
        tenant = Tenant.objects.select_related('customer', 'customer__user', 'permanent_address').get(pk=pk)
    except Tenant.DoesNotExist:
        return render(request, 'bookings/onboard_form.html', {'msg': 'Tenant not found.'})

    booking = tenant.current_booking
    if booking:
        return render(request, 'bookings/onboard_form.html', {'msg': 'Booking already exists.'})

    area_manager = AreaManager.objects.get(user=request.user)
    houses = area_manager.houses.all()
    return render(request, 'bookings/onboard_form.html', {'tenant': tenant, 'booking': booking, 'houses': houses})


@area_manager_login_required
@require_http_methods(['POST'])
def create_existing_tenant_booking_view(request):
    data = request.POST
    tenant = get_object_or_404(Tenant, pk=int(data.get('tenant')))
    space = get_object_or_404(Space, pk=int(data.get('space')))

    token_amount = float(data.get('token_amount', TOKEN_AMOUNT))
    onboarding_charges = float(data.get('onboarding_charges', ONBOARDING_CHARGES))
    rent = float(data.get('rent'))
    security_deposit = float(data.get('security_deposit'))

    original_license_start_date = get_datetime(data.get('original_license_start_date'))
    license_start_date = get_datetime(data.get('license_start_date'))
    license_end_date = get_datetime(data.get('license_end_date'))

    security_deposit_held_by_owner = data.get('security_deposit_held_by_owner') == 'on'

    if security_deposit_held_by_owner:
        booking_security_deposit = 0
    else:
        booking_security_deposit = security_deposit

    # create new booking
    booking = Booking.objects.create(tenant=tenant, space=space, type=EXISTING_TENANT_BOOKING,
                                     license_start_date=license_start_date, rent=rent,
                                     token_amount=token_amount, onboarding_charges=onboarding_charges,
                                     security_deposit=booking_security_deposit, license_end_date=license_end_date)

    # create existing tenant onboarding
    ExistingTenantOnboarding.objects.create(booking=booking, rent=rent, security_deposit=security_deposit,
                                            original_license_start_date=original_license_start_date,
                                            security_deposit_held_by_owner=security_deposit_held_by_owner)
    return JsonResponse({'detail': 'done'})


@area_manager_login_required
@require_http_methods(['GET'])
def monthly_rents_page(request, pk):
    try:
        tenant = Tenant.objects.select_related('customer', 'customer__user', 'permanent_address').get(pk=pk)
    except Tenant.DoesNotExist:
        return render(request, 'bookings/monthly_rents_page.html', {'msg': 'Tenant not found.'})

    if request.GET.get('booking'):
        booking = Booking.objects.filter(id=int(request.GET.get('booking'))).first()
    else:
        booking = tenant.current_booking
    if not booking:
        return render(request, 'bookings/monthly_rents_page.html', {'msg': 'No booking found.'})

    monthly_rents = booking.monthly_rents.select_related('payment').exclude(status=CANCELLED)

    return render(request, 'bookings/monthly_rents_page.html', {'tenant': tenant, 'booking': booking,
                                                                'monthly_rents': monthly_rents})


@area_manager_login_required
@require_http_methods(['POST'])
def create_monthly_rent_view(request):
    data = request.POST
    try:
        booking = Booking.objects.get(id=int(data.get('booking')), tenant__id=int(data.get('tenant')))
    except Booking.DoesNotExist:
        return JsonResponse({"detail": "Something went wrong!"})
    rent = float(data.get('rent'))
    start_date = get_datetime(data.get('start_date'))
    MonthlyRent.objects.create(booking=booking, rent=rent, start_date=start_date)
    return JsonResponse({'detail': 'done'})


@area_manager_login_required
@require_http_methods(['POST'])
def delete_monthly_rent_view(request):
    data = request.POST
    try:
        booking = Booking.objects.get(id=int(data.get('booking_id')))
        monthly_rent = MonthlyRent.objects.get(id=int(data.get('monthly_rent_id')), booking=booking)
    except (Booking.DoesNotExist, MonthlyRent.DoesNotExist):
        return JsonResponse({"detail": "Something went wrong!"})

    monthly_rent.payment.status = CANCELLED
    monthly_rent.payment.save()
    return JsonResponse({"detail": "Successfully deleted the monthly rent."})


@area_manager_login_required
@require_http_methods(['GET'])
def cash_collection_page(request):
    pending_cash_payments = TenantPayment.objects.select_related('booking__space__house', 'booking__tenant',
                                                                 'booking__tenant__customer', 'transaction',
                                                                 'booking__space__house__address',
                                                                 'booking__tenant__customer__user'
                                                                 ).filter(transaction__payment_gateway=CASH,
                                                                          transaction__collector=request.user,
                                                                          status=PENDING).order_by(
        'transaction__collection_time_start')

    msg = None
    if len(pending_cash_payments) is 0:
        msg = "No pending cash collections!"
    return render(request, 'cash_collections/cash_collection_form.html',
                  {'payments': pending_cash_payments, 'msg': msg})


@area_manager_login_required
@require_http_methods(['POST'])
def cash_collection_confirmation_view(request, pk):
    payment = get_object_or_404(TenantPayment, pk=pk, transaction__collector=request.user)
    payment.transaction.actual_collection_time = timezone.now()
    payment.transaction.complete = True
    payment.transaction.save()
    return JsonResponse({'detail': 'Cash collection successful.'})


@area_manager_login_required
@require_http_methods(['GET', 'POST'])
def cash_deposit_page(request):
    if request.method == 'GET':
        pending_cash_deposits = CustomerTransaction.objects.filter(payment_gateway=CASH,
                                                                   collector=request.user,
                                                                   complete=True, deposited=False)
        msg = None
        if len(pending_cash_deposits) is 0:
            msg = "No pending cash deposits!"
        return render(request, 'cash_collections/cash_deposit_form.html',
                      {'deposits': pending_cash_deposits, 'msg': msg})

    elif request.method == 'POST':
        deposit_note = request.POST.get('deposit_note')
        transaction_ids = list(map(int, request.POST.getlist('checked')))
        transactions = CustomerTransaction.objects.filter(id__in=transaction_ids)
        for transaction in transactions:
            transaction.deposited = True
            transaction.deposit_time = timezone.now()
            transaction.deposit_reference = deposit_note
            transaction.deposit_reference_image = request.FILES.get('deposit_reference_image')
            transaction.save()
        return JsonResponse({'detail': 'Successfully saved the cash deposit details!'})


@area_manager_login_required
@require_http_methods(['GET', 'POST'])
def house_visits_page(request):
    if request.method == 'GET':
        house_visits = HouseVisit.objects.select_related('house', 'house__address',
                                                         'customer', 'customer__user'
                                                         ).filter(area_manager__user=request.user,
                                                                  cancelled=False)
        pending_house_visits = house_visits.filter(visited=False)
        completed_house_visits = house_visits.filter(visited=True).order_by('-id')[:10]
        return render(request, 'houses/house_visit_form.html', {'pending_visits': pending_house_visits,
                                                                'completed_visits': completed_house_visits})

    elif request.method == 'POST':
        house_visit = get_object_or_404(HouseVisit, area_manager__user=request.user, id=request.POST.get('id'))
        house_visit.visited = True
        house_visit.actual_visit_time = timezone.now()
        house_visit.area_manager_notes = request.POST.get('note')
        house_visit.save()
        return JsonResponse({'detail': 'done'})


@area_manager_login_required
def house_bookings_page(request, pk):
    try:
        house = House.objects.get(pk=pk)
    except House.DoesNotExist:
        return render(request, 'houses/house_bookings_page.html', {'msg': "No house found."})

    bookings = Booking.objects.filter(space__house=house, status=BOOKING_COMPLETE, moved_out=False)
    return render(request, 'houses/house_bookings_page.html', {'house': house, 'bookings': bookings})


@area_manager_login_required
@require_http_methods(['GET', 'POST'])
def house_index_page(request):
    if request.method == 'GET':
        return render(request, 'houses/house_edit_page.html')

    elif request.method == 'POST':
        house_id = request.POST.get('house_id')
        return redirect(house_main_page, pk=house_id)


@area_manager_login_required
@require_http_methods(['GET'])
def house_main_page(request, pk):
    try:
        house = House.objects.get(pk=pk)
    except House.DoesNotExist:
        return render(request, 'houses/house_edit_page.html', {'msg': "House with Id {} does not exist.".format(pk)})

    space_types = HouseAccomodationTypeCategories[::-1]
    space_subtypes = SpaceSubType.objects.all()[::-1]

    # preparing private room data
    private_rooms = house.private_rooms.all()
    private_room_subtypes = SpaceSubType.objects.filter(
        id__in=private_rooms.values_list('space__subtype', flat=True).distinct())

    private_room_data = {}
    for subtype in private_room_subtypes:
        private_room_data[subtype.name] = private_rooms.filter(space__subtype=subtype)

    # preparing shared room data
    shared_rooms = house.shared_rooms.all()
    shared_room_subtypes = SpaceSubType.objects.filter(
        id__in=shared_rooms.values_list('space__subtype', flat=True).distinct())

    shared_room_data = {}
    for subtype in shared_room_subtypes:
        shared_room_data[subtype.name] = shared_rooms.filter(space__subtype=subtype)

    # preparing flats data
    flats = house.flats.all()
    flat_subtypes = SpaceSubType.objects.filter(
        id__in=flats.values_list('space__subtype', flat=True).distinct())

    flat_data = {}
    for subtype in flat_subtypes:
        flat_data[subtype.name] = flats.filter(space__subtype=subtype)

    return render(request, 'houses/house_edit_page.html', {'house': house,
                                                           'private_room_subtypes': private_room_subtypes,
                                                           'private_rooms': private_room_data,
                                                           'shared_room_subtypes': shared_room_subtypes,
                                                           'shared_rooms': shared_room_data,
                                                           'flat_subtypes': flat_subtypes,
                                                           'flats': flat_data,
                                                           'space_types': space_types,
                                                           'space_subtypes': space_subtypes})


@area_manager_login_required
@require_http_methods(['POST'])
def create_house_spaces_view(request, pk):
    house = get_object_or_404(House, pk=pk)
    space_type = request.POST.get('space_type')
    space_subtype = get_object_or_404(SpaceSubType, pk=int(request.POST.get('space_subtype')))
    if space_type == SHARED_ROOM:
        bed_count = int(request.POST.get('bed_count'))
    else:
        bed_count = None
    duplicate_count = int(request.POST.get('duplicate_count', 1))
    space_name_prefix = request.POST.get('space_name_prefix')
    space_name_initial_count = int(request.POST.get('space_name_initial_count', 1))

    existing_space = house.spaces.filter(subtype=space_subtype).first()
    if existing_space:
        rent = existing_space.rent
        security_deposit = existing_space.security_deposit
        commission = existing_space.commission
    else:
        rent, security_deposit, commission = 0, 0, 0

    for i in range(duplicate_count):
        space = Space.objects.create(house=house,
                                     name="{} {}".format(space_name_prefix, i + space_name_initial_count),
                                     type=space_type,
                                     subtype=space_subtype,
                                     rent=rent,
                                     security_deposit=security_deposit,
                                     commission=commission)
        if space.type == SHARED_ROOM:
            space.shared_room.bed_count = bed_count
            space.shared_room.save()
    return JsonResponse({'detail': 'Successfully created new spaces!'})


@area_manager_login_required
@require_http_methods(['POST'])
def delete_house_space_view(request, pk):
    house = get_object_or_404(House, pk=pk)
    space = get_object_or_404(Space, house=house, pk=int(request.POST.get('space_id')))
    if space.availability != AVAILABLE:
        return JsonResponse({'detail': "Can't delete the space."})
    if space.type == SHARED_ROOM:
        if any([bed.availability != AVAILABLE for bed in space.shared_room.beds.all()]):
            return JsonResponse({'detail': "Can't delete the space. Bed not empty."})
        space.shared_room.beds.all().delete()
        space.shared_room.delete()
    elif space.type == PRIVATE_ROOM:
        space.private_room.delete()
    elif space.type == FLAT:
        space.flat.delete()
    space.delete()
    return JsonResponse({'detail': 'Space deleted successfully!'})


@area_manager_login_required
@require_http_methods(['POST'])
def update_house_subtype_spaces_view(request, pk):
    house = get_object_or_404(House, pk=pk)
    space_subtype = get_object_or_404(SpaceSubType, pk=int(request.POST.get('space_subtype')))
    spaces = Space.objects.filter(house=house, subtype=space_subtype)
    data = {
        'rent': float(request.POST.get('rent')),
        'security_deposit': float(request.POST.get('security_deposit')),
        'commission': float(request.POST.get('commission'))
    }
    spaces.update(**data)
    return JsonResponse({'detail': 'done'})


@area_manager_login_required
@require_http_methods(['POST'])
def send_sms_view(request):
    phone_no = request.POST.get('phone_no')
    msg = request.POST.get('msg')
    if phone_no and msg:
        send_sms.delay(phone_no, msg)
    return JsonResponse({'detail': 'done'})


@area_manager_login_required
@csrf_exempt
def multiple_space_update_view(request):
    queryset = Space.objects.all()
    selected_house = None
    if 'house' in request.GET:
        queryset = queryset.filter(house_id=request.GET['house'])
        selected_house = House.objects.get(id=request.GET['house'])

    form_set = modelformset_factory(model=Space, form=SpaceUpdateForm, extra=0)
    post_form_set = form_set(request.POST or None, queryset=queryset)

    success_msg = None
    error_msg = None
    if request.method == 'POST':
        if post_form_set.is_valid():
            post_form_set.save()
            success_msg = 'Updated Succesfully'
        else:
            error_msg = str(post_form_set.errors)

    context = {
        'spaces': queryset,
        'houses': House.objects.all(),
        'selected_house': selected_house,
        'form_set': post_form_set,
        'success_msg': success_msg,
        'error_msg': error_msg
    }

    return render(request, 'houses/house_space_edit_page.html', context=context)
