from datetime import timedelta

from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from Homes.Houses.utils import PENDING_HOUSE_VISIT_MSG, HOUSE_VISIT_RESCHEDULE_DAYS_LIMIT, RESCHEDULE_HOUSE_VISIT_MSG, \
    CANCEL_HOUSE_VISIT_MSG
from Homes.scout_task_utils import send_scout_task_to_scout_backend
from utility.logging_utils import sentry_debug_logger
from utility.sms_utils import send_sms

logger = get_task_logger(__name__)


@shared_task(bind=True)
@periodic_task(run_every=crontab(minute=0, hour='3'))
def pending_house_visit_notify():
    from Homes.Houses.models import HouseVisit
    house_visits = HouseVisit.objects.filter(visited=False, cancelled=False)

    for house_visit in house_visits:
        customer = house_visit.customer
        house = house_visit.house
        area_manager = house_visit.area_manager
        if area_manager is None:
            continue
        logger.info("Sending pending house visit SMS to customer @ {}".format(customer.phone_no))
        msg = PENDING_HOUSE_VISIT_MSG.format(customer.user.first_name, house.address.complete_address,
                                             house_visit.scheduled_visit_time.strftime("%I %p"),
                                             area_manager.name, area_manager.phone_no)
        try:
            send_sms(customer.phone_no, msg)
            logger.info("Sent pending house visit SMS to customer @ {}".format(customer.phone_no))
        except Exception as e:
            logger.error(e)


@shared_task(bind=True)
@periodic_task(run_every=crontab(minute=0, hour='15'))
def reschedule_house_visit_notify():
    from Homes.Houses.models import HouseVisit
    house_visits = HouseVisit.objects.filter(visited=False, cancelled=False, scheduled_visit_time__lt=timezone.now())

    for house_visit in house_visits:
        customer = house_visit.customer
        house = house_visit.house

        if timezone.now() - house_visit.scheduled_visit_time <= timedelta(days=HOUSE_VISIT_RESCHEDULE_DAYS_LIMIT):
            msg = RESCHEDULE_HOUSE_VISIT_MSG.format(customer.user.first_name, house.address.complete_address,
                                                    house_visit.scheduled_visit_time.strftime("%I %p"))
        else:
            house_visit.cancelled = True
            house_visit.save()
            msg = CANCEL_HOUSE_VISIT_MSG.format(customer.user.first_name, house.address.complete_address)

        logger.info("Sending reschedule/cancel house visit SMS to customer @ {}".format(customer.phone_no))
        try:
            send_sms(customer.phone_no, msg)
            logger.info("Sent reschedule/cancel house visit SMS to customer @ {}".format(customer.phone_no))
        except Exception as e:
            logger.error(e)


@shared_task
def notify_scout_visit_cancelled(house_visit_id):
    try:
        from Homes.Houses.models import HouseVisit
        from Homes.Houses.utils import HOUSE_VISIT_CANCELLED
        house_visit = HouseVisit.objects.filter(id=house_visit_id).first()
        sentry_debug_logger.debug("house visit is " + str(house_visit))
        if house_visit:
            data = {'house_id': house_visit.house.id, 'visit_id': house_visit.id}
            task_type = HOUSE_VISIT_CANCELLED
            send_scout_task_to_scout_backend(data=data, task_type=task_type)
    except Exception as E:
        sentry_debug_logger.debug('error occurred while sending scout_task_for_house_visit  ' + str(E), exc_info=True)
