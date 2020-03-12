from datetime import datetime

import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from decouple import config
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import sendgrid, Email
from sendgrid.helpers.mail import Content, Mail

from utility.environments import PRODUCTION

logger = get_task_logger(__name__)


@shared_task
def send_monthly_earning_invoice_email(monthly_earning_id):
    from Homes.Owners.models import OwnerMonthlyEarning
    monthly_earning = OwnerMonthlyEarning.objects.get(id=monthly_earning_id)
    email = monthly_earning.owner.user.email
    logger.info("Sending monthly rent invoice email to owner @ {}".format(email))

    sg = sendgrid.SendGridAPIClient(apikey=config("SENDGRID_API_KEY"))
    from_email = Email("Halanx <support@halanx.com>")
    to_email = Email(email)
    subject = "Monthly Rent Invoice #{}".format(monthly_earning.id)
    html_content = render_to_string('monthly_earning_invoice.html',
                                    {'monthly_earning': monthly_earning, 'timestamp': datetime.now()})
    content = Content("text/html", html_content)
    mail = Mail(from_email, subject, to_email, content)
    try:
        sg.client.mail.send.post(request_body=mail.get())
        logger.info("Sent monthly rent invoice email to owner @ {}".format(email))
    except Exception as e:
        logger.error(e)


@shared_task
def send_owner_payment_confirmation_email(payment_id):
    from Homes.Owners.models import OwnerPayment
    payment = OwnerPayment.objects.get(id=payment_id)
    email = payment.wallet.owner.user.email
    logger.info("Sending payment confirmation email to owner @ {}".format(email))

    sg = sendgrid.SendGridAPIClient(apikey=config("SENDGRID_API_KEY"))
    from_email = Email("Halanx <support@halanx.com>")
    to_email = Email(email)
    subject = "Owner Payment #{}".format(payment.id)
    html_content = render_to_string('owner_payment_confirm.html',
                                    {'payment': payment})
    content = Content("text/html", html_content)
    mail = Mail(from_email, subject, to_email, content)
    try:
        sg.client.mail.send.post(request_body=mail.get())
        logger.info("Sent payment confirmation email to owner @ {}".format(email))
    except Exception as e:
        logger.error(e)


@shared_task
def add_affiliate_referral_task_owner_listing(owner_listing_id):
    """
    Task to add owner listing to affiliate referrals
    """
    logger.info('Started add affiliate referral task for owner listing id {}'.format(owner_listing_id))

    from Homes.Owners.models import OwnerListing
    owner_listing = OwnerListing.objects.get(id=owner_listing_id)

    if not owner_listing.affiliate_code:
        # change affiliate code to default halanx code
        owner_listing.affiliate_code = config("HALANX_AFFILIATE_DEFAULT_REFERRAL_CODE")
        owner_listing.save()

    if owner_listing.affiliate_code is not None:

        from Homes.Owners.api.serializers import OwnerListingSerializer
        from utility.logging_utils import sentry_debug_logger

        data = OwnerListingSerializer(owner_listing).data
        data['source'] = config('HALANX_AFFILIATE_SOURCE')
        url = (config('HALANX_AFFILIATE_API_ENDPOINT') if settings.ENVIRONMENT == PRODUCTION else
        config('HALANX_AFFILIATE_TEST_API_ENDPOINT')) + config('HALANX_AFFILIATE_OWNER_REFERRAL_API')
        resp = requests.post(url, data=data)
        print(resp.text)
        sentry_debug_logger.debug('url is ' + str(url) + 'data is' + str(data) + 'response is ' + str(resp.content))

    logger.info('Finished add affiliate referral task for owner listing id {}'.format(owner_listing_id))
