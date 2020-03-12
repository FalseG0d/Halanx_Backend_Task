from datetime import datetime, timedelta

import requests
from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger
from decouple import config
from django.template.loader import render_to_string
from django.utils import timezone
from sendgrid import sendgrid, Email
from sendgrid.helpers.mail import Content, Mail

from Common.utils import PENDING
from Homes.Bookings.utils import BOOKING_COMPLETE, LATE_MONTHLY_RENT_FINE_AMOUNT, BOOKING_CANCELLATION_MSG, BOOKING
from Homes.Tenants.models import TenantPayment, TenantRequirement
from utility.cross_project_task_utils import TASK_TYPE, UPDATE_LEAD_REFERRAL_STATUS, SUB_TASK
from utility.render_response_utils import STATUS, DATA
from utility.sms_utils import send_sms

logger = get_task_logger(__name__)


@shared_task
def send_booking_invoice_email(booking_id):
    from Homes.Bookings.models import Booking
    booking = Booking.objects.get(id=booking_id)
    email = booking.tenant.customer.user.email
    logger.info("Sending booking invoice email to tenant @ {}".format(email))

    sg = sendgrid.SendGridAPIClient(apikey=config("SENDGRID_API_KEY"))
    from_email = Email("Halanx <support@halanx.com>")
    to_email = Email(email)
    subject = "House Booking Invoice #{}".format(booking.id)
    html_content = render_to_string('booking_invoice.html',
                                    {'booking': booking, 'timestamp': datetime.now()})
    content = Content("text/html", html_content)
    mail = Mail(from_email, subject, to_email, content)
    try:
        sg.client.mail.send.post(request_body=mail.get())
        logger.info("Sent booking invoice email to tenant @ {}".format(email))
    except Exception as e:
        logger.error(e)


@shared_task
def send_booking_cancellation_sms(booking_id, cancellation_reason):
    from Homes.Bookings.models import Booking
    booking = Booking.objects.get(id=booking_id)
    customer = booking.tenant.customer
    phone_no = customer.phone_no
    logger.info("Sending booking cancellation SMS to tenant @ {}".format(phone_no))
    msg = BOOKING_CANCELLATION_MSG.format(customer.user.first_name, booking.space.type, booking.space.house.name,
                                          cancellation_reason)
    try:
        send_sms(phone_no, msg)
        logger.info("Sent booking cancellation SMS to tenant @ {}".format(phone_no))
    except Exception as e:
        logger.error(e)


@shared_task(bind=True)
@periodic_task(run_every=crontab(minute=0, hour='12'))
def create_update_monthly_rent():
    from Homes.Bookings.models import Booking, MonthlyRent

    # create monthly rent
    bookings = Booking.objects.filter(status=BOOKING_COMPLETE, moved_out=False)
    for booking in bookings:
        last_monthly_rent = booking.monthly_rents.last()
        if booking.license_end_date and booking.license_end_date <= last_monthly_rent.start_date + timedelta(days=31):
            continue
        if timezone.now() - last_monthly_rent.start_date >= timedelta(days=27):
            MonthlyRent(booking=booking, start_date=last_monthly_rent.start_date + timedelta(days=30)).save()

    # set fine on monthly rent
    monthly_rents = MonthlyRent.objects.filter(status=PENDING)
    for monthly_rent in monthly_rents:
        delay = round((timezone.now() - monthly_rent.due_date).seconds / (24 * 60 * 60))
        monthly_rent.payment.fine = LATE_MONTHLY_RENT_FINE_AMOUNT * delay
        monthly_rent.payment.save()
        monthly_rent.save()


@shared_task(bind=True)
@periodic_task(run_every=crontab(minute=0, hour='8,20'))
def pending_tenant_payment_notify():
    tenant_payments = TenantPayment.objects.select_related('wallet__tenant__customer',
                                                           'wallet__tenant__customer__user').filter(status=PENDING)
    for tenant_payment in tenant_payments:
        message = "Hi {}! You have a pending payment of Rs {} as {}\nDue date: {}".format(
            tenant_payment.wallet.tenant.name, tenant_payment.amount, tenant_payment.description,
            tenant_payment.due_date.strftime("%d %b, %Y"))
        # send_sms(tenant_payment.wallet.tenant.customer.phone_no, message)


@shared_task
def update_affiliate_conversion_details_to_lead_tool(booking_id=None):
    from utility.logging_utils import sentry_debug_logger
    try:
        if booking_id:
            from Homes.Bookings.models import Booking
            booking = Booking.objects.filter(id=booking_id).first()
            if booking:
                if booking.status == BOOKING_COMPLETE:
                    tenant = booking.tenant
                    if tenant:
                        tenant_requirement = TenantRequirement.objects.filter(tenant=tenant).first()
                        if tenant_requirement:
                            if tenant_requirement.affiliate_code:
                                print("send booking details to affiliate tool via lead tool with code" +
                                      str(tenant_requirement.affiliate_code))

                                from Homes.Tenants.api.serializers import TenantRequirementSerializer
                                request_data = {
                                    TASK_TYPE: UPDATE_LEAD_REFERRAL_STATUS,
                                    SUB_TASK: BOOKING,
                                    STATUS: BOOKING_COMPLETE,
                                    DATA: TenantRequirementSerializer(tenant_requirement).data
                                }

                                url = config('HALANX_LEAD_API_ENDPOINT') + config('HALANX_LEAD_UPDATE_TENANT_REFERRAL_API')
                                resp = requests.post(url, data=request_data)

                                sentry_debug_logger.debug(
                                    'updating conversion  url is ' + str(url) + 'data is' + str(
                                        request_data) + 'response is ' + str(resp.content))

    except Exception as E:
        sentry_debug_logger.debug('error occured while updating affiliate converion due to ' + str(E), exc_info=True)
