import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from decouple import config


logger = get_task_logger(__name__)


@shared_task
def send_sms(phone_no, message):

    logger.info("Sending SMS to phone number {}".format(phone_no))

    authkey = config('MSG91_AUTH_KEY')
    sender = 'halanx'
    data = {
        'authkey': authkey,
        'mobiles': phone_no,
        'message': message,
        'sender': sender,
        'route': '4'
    }
    url = config('MSG91_API_URL')
    res = requests.post(url, data=data)

    logger.info("Sent SMS to phone number {} with response: {}".format(phone_no, res.text))
