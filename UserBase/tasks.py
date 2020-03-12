from datetime import timedelta, datetime
# noinspection SpellCheckingInspection,PyCompatibility
from urllib import request as urllibrequest

from allauth.socialaccount.models import SocialAccount
from celery import shared_task
from celery.utils.log import get_task_logger
from decouple import config
from django.core.files import File
from django.template.loader import render_to_string
from django.utils import timezone
from sendgrid import sendgrid, Email
from sendgrid.helpers.mail import Content, Mail

from Notifications.models import Notification
from Notifications.utils import PLACE_VISIT_NC
from Places.models import Place, Visit
from UserBase.models import Customer, UserLocation, Picture
from UserBase.utils import FB_PROFILE_PIC_URL
from utility.geo_utils import find_distance

logger = get_task_logger(__name__)


@shared_task
def send_welcome_mail(username, email):
    logger.info("Sending welcome email to customer @ {}".format(email))

    sg = sendgrid.SendGridAPIClient(apikey=config("SENDGRID_API_KEY"))
    from_email = Email("Halanx <support@halanx.com>")
    to_email = Email(email)
    subject = "Welcome to Halanx"
    html_content = render_to_string('htmlemail/welcome-embedded.html',
                                    {'name': username, 'email': email,
                                     'site': 'https://d28fujbigzf56k.cloudfront.net'})
    content = Content("text/html", html_content)
    mail = Mail(from_email, subject, to_email, content)
    try:
        sg.client.mail.send.post(request_body=mail.get())
        logger.info("Sent welcome email to customer @ {}".format(email))
    except Exception as e:
        logger.error(e)


@shared_task
def send_email_otp(email, otp):
    logger.info("Sending email otp to customer @ {}".format(email))

    sg = sendgrid.SendGridAPIClient(apikey=config("SENDGRID_API_KEY"))
    from_email = Email("Halanx <support@halanx.com>")
    to_email = Email(email)
    subject = "Welcome to Halanx"
    html_content = render_to_string('htmlemail/email_otp_verify.html',
                                    {'name': '', 'email': email,
                                     'otp': str(otp),
                                     'site': 'https://d28fujbigzf56k.cloudfront.net'})

    content = Content("text/html", html_content)
    mail = Mail(from_email, subject, to_email, content)
    try:
        sg.client.mail.send.post(request_body=mail.get())
        logger.info("Sent welcome email to customer @ {}".format(email))
    except Exception as e:
        logger.error(e)


@shared_task
def track_customer_visit(customer_id):
    logger.info("Starting customer visit tracking for customer id {}".format(customer_id))

    customer = Customer.objects.get(id=customer_id)

    # get current location of customer
    latitude = customer.clatitude
    longitude = customer.clongitude

    curr = timezone.now()
    # check if no new user location recorded in last 2 minutes
    if not customer.locations.filter(timestamp__gte=curr - timedelta(minutes=2)).count():

        # create new user location record
        UserLocation.objects.create(customer=customer, latitude=latitude, longitude=longitude)

        # get latest user location between last 10-60 minutes
        latest = customer.locations.filter(timestamp__lte=curr - timedelta(minutes=10),
                                           timestamp__gte=curr - timedelta(minutes=60)).last()

        if latest:
            dis = find_distance((latest.latitude, latest.longitude), (latitude, longitude)).m
            if dis <= 100:
                # find places nearby visit point
                nearby_places = Place.objects.nearby(latitude, longitude)
                if len(nearby_places):
                    place = nearby_places[0][0]
                    today = datetime.strftime(curr, "%Y-%m-%d")
                    # check if customer has visited that place today already
                    if not customer.visits.filter(place=place, timestamp__date=today).count():
                        # create new visit and send notification to create checkin
                        Visit(visitor=customer, place=place).save()
                        Notification(target=customer, category=PLACE_VISIT_NC).save({"place_name": place.name,
                                                                                     "place_id": place.id})

    logger.info("Finished customer visit tracking for customer id {}".format(customer_id))


@shared_task
def set_profile_pic_from_social_account(customer_id):
    logger.info("Setting profile pic from social account for customer id {}".format(customer_id))
    return
    customer = Customer.objects.get(id=customer_id)
    fb_id = SocialAccount.objects.get(user=customer.user).uid
    img_url = FB_PROFILE_PIC_URL.format(fb_id)
    img_file = urllibrequest.urlretrieve(img_url)
    profile_pic = Picture(customer=customer, is_profile_pic=True)
    profile_pic.image.save('{}.jpg'.format(customer.user.username), File(open(img_file[0], 'rb')))
    profile_pic.save()

    logger.info("Done setting profile pic from social account for customer id {}".format(customer_id))
