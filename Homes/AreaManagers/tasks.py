from datetime import timedelta

from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from Homes.AreaManagers.models import AreaManager
from Homes.AreaManagers.utils import AREA_MANAGER_CASH_COLLECTION_NOTIFY_MSG, AREA_MANAGER_HOUSE_VISIT_NOTIFY_MSG, \
    AREA_MANAGER_NEW_HOUSE_VISIT_NOTIFY_MSG
from Homes.scout_task_utils import send_scout_task_to_scout_backend
from Homes.Houses.utils import HOUSE_VISIT
from utility.logging_utils import sentry_debug_logger
from utility.online_transaction_utils import CASH
from utility.sms_utils import send_sms

logger = get_task_logger(__name__)


def send_house_visit_sms_and_send_scout_task(house_visit, area_manager, new=True):
    customer = house_visit.customer
    house = house_visit.house
    logger.info("Sending house visit SMS to area manager @ {}".format(area_manager.phone_no))
    if new:
        msg = AREA_MANAGER_NEW_HOUSE_VISIT_NOTIFY_MSG.format(name=customer.name, phone_no=customer.phone_no,
                                                             time=house_visit.scheduled_visit_time.strftime("%d %b at "
                                                                                                            "%I %p"),
                                                             house="{}, {}".format(house.name, house.address))
    else:
        msg = AREA_MANAGER_HOUSE_VISIT_NOTIFY_MSG.format(name=customer.name,
                                                         phone_no=customer.phone_no,
                                                         time=house_visit.scheduled_visit_time.strftime("%I %p"),
                                                         house="{}, {}".format(house.name, house.address))
    try:
        send_sms(area_manager.phone_no, msg)
        logger.info("Sent house visit SMS to area manager @ {}".format(area_manager.phone_no))
    except Exception as e:
        logger.error(e)

    try:
        data = {'house_id': house.id, 'visit_id': house_visit.id}
        task_type = HOUSE_VISIT
        send_scout_task_to_scout_backend(data=data, task_type=task_type)
    except Exception as E:
        sentry_debug_logger.debug('error occurred while sending scout_task_for_house_visit  ' + str(E), exc_info=True)


@shared_task
def area_manager_house_visit_notify(house_visit_id):
    from Homes.Houses.models import HouseVisit
    sentry_debug_logger.debug('house visit id is ' + str(house_visit_id), exc_info=True)
    house_visit = HouseVisit.objects.get(id=house_visit_id)
    area_manager = house_visit.area_manager
    if area_manager:
        send_house_visit_sms_and_send_scout_task(house_visit, area_manager)


@shared_task(bind=True)
@periodic_task(run_every=crontab(minute=0, hour='3'))
def upcoming_house_visits_notify():
    from Homes.Houses.models import HouseVisit
    house_visits = HouseVisit.objects.filter(visited=False, cancelled=False)
    for house_visit in house_visits:
        area_manager = house_visit.area_manager
        if area_manager is None:
            continue
        send_house_visit_sms_and_send_scout_task(house_visit, area_manager, new=False)


def send_cash_collection_sms(payment):
    tenant = payment.wallet.tenant
    house = payment.booking.space.house
    transaction = payment.transaction
    area_manager = AreaManager.objects.get(user=payment.transaction.collector)
    logger.info("Sending cash collection SMS to area manager @ {}".format(area_manager.phone_no))
    msg = AREA_MANAGER_CASH_COLLECTION_NOTIFY_MSG.format(name=tenant.name,
                                                         phone_no=tenant.phone_no,
                                                         amount=transaction.amount,
                                                         house="{}, {}".format(house.name, house.address),
                                                         time=transaction.collection_time_start.strftime("%d %b at "
                                                                                                         "%I %p"))
    try:
        send_sms(area_manager.phone_no, msg)
        logger.info("Sent cash collection SMS to area manager @ {}".format(area_manager.phone_no))
    except Exception as e:
        logger.error(e)


@shared_task
def area_manager_cash_collection_notify(transaction_id):
    from Homes.Tenants.models import TenantPayment
    payment = TenantPayment.objects.filter(transaction__id=transaction_id).first()
    if payment:
        send_cash_collection_sms(payment)


@shared_task(bind=True)
@periodic_task(run_every=crontab(minute=0, hour='3'))
def upcoming_cash_collections_notify():
    from Transaction.models import CustomerTransaction
    transactions = CustomerTransaction.objects.filter(complete=False, cancelled=False, payment_gateway=CASH,
                                                      collection_time_start__gte=timezone.now(),
                                                      collection_time_start__lte=timezone.now() + timedelta(hours=24))
    for transaction in transactions:
        from Homes.Tenants.models import TenantPayment
        payment = TenantPayment.objects.filter(transaction=transaction).first()
        if payment:
            send_cash_collection_sms(payment)
