import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from decouple import config
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import sendgrid, Email
from sendgrid.helpers.mail import Content, Mail

from Common.utils import PAID
from Homes.Tenants.utils import TENANT_REFERRER_CASHBACK_AMOUNT, SUCCESSFUL_TENANT_PAYMENT_MSG, MOVE_OUT
from Homes.scout_task_utils import send_scout_task_to_scout_backend
from Notifications.models import Notification
from Notifications.utils import TENANT_PAYMENT_SUCCESSFUL_NC, CASHBACK_NC
from utility.environments import PRODUCTION
from utility.logging_utils import sentry_debug_logger
from utility.sms_utils import send_sms

logger = get_task_logger(__name__)


@shared_task
def add_affiliate_referral_task(tenant_requirement_id):
    """
    Task to add tenant referral to affiliate referrals
    :param tenant_requirement_id:
    """
    logger.info('Started add affiliate referral task for tenant requirement id {}'.format(tenant_requirement_id))

    from Homes.Tenants.models import TenantRequirement
    tenant_requirement = TenantRequirement.objects.get(id=tenant_requirement_id)

    if not tenant_requirement.affiliate_code:
        tenant_requirement.affiliate_code = config("HALANX_AFFILIATE_DEFAULT_REFERRAL_CODE")
        tenant_requirement.save()

    if tenant_requirement.affiliate_code is not None:

        # change affiliate code to default halanx code
        from Homes.Tenants.api.serializers import TenantRequirementSerializer
        data = TenantRequirementSerializer(tenant_requirement).data
        data['source'] = config('HALANX_AFFILIATE_SOURCE')
        url = (config('HALANX_AFFILIATE_API_ENDPOINT') if settings.ENVIRONMENT == PRODUCTION else
        config('HALANX_AFFILIATE_TEST_API_ENDPOINT')) + config('HALANX_AFFILIATE_TENANT_REFERRAL_API')
        resp = requests.post(url, data=data)
        logger.info(resp.text)
        print(resp.text)
        from utility.logging_utils import sentry_debug_logger
        sentry_debug_logger.debug('url is ' + str(url) + 'data is' + str(data) + 'response is ' + str(resp.content))
    logger.info('Finished add affiliate referral task for tenant requirement id {}'.format(tenant_requirement_id))


@shared_task
def tenant_referrer_cashback_task(wallet_id):
    """
    Task to give hcash to referrer of tenant if tenant has done his/her first payment.
    :param wallet_id: wallet id of tenant
    """
    logger.info('Started tenant referrer cashback task for wallet id {}'.format(wallet_id))

    from Homes.Tenants.models import TenantWallet
    wallet = TenantWallet.objects.get(id=wallet_id)

    if wallet.payments.filter(status=PAID).count() == 1 and wallet.tenant.referrer is not None:
        friend = wallet.tenant.referrer.customer
        friend.hcash += TENANT_REFERRER_CASHBACK_AMOUNT
        friend.save()
        notification_payload = {'amount': TENANT_REFERRER_CASHBACK_AMOUNT}
        Notification(target=friend, category=CASHBACK_NC, payload=notification_payload).save(
            data={'amount': TENANT_REFERRER_CASHBACK_AMOUNT})

    logger.info('Finished tenant referrer cashback task for wallet id {}'.format(wallet_id))


@shared_task
def send_tenant_payment_confirmations(payment_id, email=True, sms=True, notification=True, payment_gateway=None):
    """
    Task to send email, sms, notification to tenant on successful payment.
    :param payment_gateway:
    :param payment_id: Tenant Payment ID
    :param email: True/False
    :param sms: True/False
    :param notification: True/False
    """
    from Homes.Tenants.models import TenantPayment
    payment = TenantPayment.objects.get(id=payment_id)
    customer = payment.wallet.tenant.customer

    if sms:
        phone_no = customer.phone_no
        logger.info("Sending payment confirmation SMS to tenant @ {}".format(phone_no))
        if payment_gateway:
            msg = SUCCESSFUL_TENANT_PAYMENT_MSG.format(customer.user.first_name, payment.description, payment.amount,
                                                       payment_gateway, payment.id)

        try:
            send_sms.delay(phone_no, msg)
            logger.info("Sent payment confirmation SMS to tenant @ {}".format(phone_no))
        except Exception as e:
            logger.error(e)

    if email:
        email = customer.user.email
        logger.info("Sending payment confirmation email to tenant @ {}".format(email))

        sg = sendgrid.SendGridAPIClient(apikey=config("SENDGRID_API_KEY"))
        from_email = Email("Halanx <support@halanx.com>")
        to_email = Email(email)
        subject = "Tenant Payment #{}".format(payment.id)
        html_content = render_to_string('tenant_payment_confirm.html',
                                        {'payment': payment})
        content = Content("text/html", html_content)
        mail = Mail(from_email, subject, to_email, content)
        try:
            sg.client.mail.send.post(request_body=mail.get())
            logger.info("Sent payment confirmation email to tenant @ {}".format(email))
        except Exception as e:
            logger.error(e)

    if notification:
        logger.info("Sending payment confirmation notification to tenant @ {}".format(customer.name))
        try:
            payload = {'amount': payment.amount}
            Notification(target=customer, category=TENANT_PAYMENT_SUCCESSFUL_NC, payload=payload
                         ).save({'amount': payment.amount,
                                 'payment_id': payment.id,
                                 'description': payment.description,
                                 'payment_gateway': payment.transaction.payment_gateway
                                 })
            logger.info("Sent payment confirmation notification to tenant @ {}".format(customer.name))
        except Exception as e:
            logger.error(e)


@shared_task
def notify_scout_new_move_out_task(tenant_moveout_requirement_id):
    try:
        from Homes.Tenants.models import TenantMoveOutRequest
        move_out_request = TenantMoveOutRequest.objects.filter(id=tenant_moveout_requirement_id).first()
        if move_out_request:
            tenant = move_out_request.tenant
            booking_id = tenant.current_booking.id
            space_id = tenant.current_booking.space.id
            house_id = tenant.current_booking.space.house.id
            move_out_request_id = move_out_request.id

            data = {'house_id': house_id, 'space_id': space_id, 'booking_id': booking_id,
                    'move_out_request_id': move_out_request_id}
            task_type = MOVE_OUT
            send_scout_task_to_scout_backend(data=data, task_type=task_type)
    except Exception as E:
        sentry_debug_logger.error('error occurred while sending scout_task_for_move_out' + str(E), exc_info=True)
