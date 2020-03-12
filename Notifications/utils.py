import json

from django.conf import settings
from pyfcm import FCMNotification

notify_user = FCMNotification(api_key=settings.GCM_API_KEY_USER).notify_single_device

PAYLOAD_KEY_USER = 'user'

INSUFFICIENT_BALANCE_1_NC = "InsufficientBalance1"
INSUFFICIENT_BALANCE_2_NC = "InsufficientBalance2"
BATCH_ACCEPTED_NC = "BatchAccepted"
BATCH_DELIVERED_NC = "BatchDelivered"
ORDER_DELIVERED_NC = "OrderDelivered"
CASHBACK_NC = "CashBack"
PROMOCODE_CASHBACK_NC = "PromoCodeCashBack"
TITLE_ASSIGNED_NC = "TitleAssigned"
ALERT_NC = "Alert"
ANNOUNCEMENT_NC = "Announcement"
PLACE_VISIT_NC = "PlaceVisit"
TENANT_PAYMENT_DUE_NC = "DueTenantPayment"
TENANT_PAYMENT_SUCCESSFUL_NC = "SuccessfulTenantPayment"
NEW_COMMENT_ON_POST_NC = "NewComment"
POST_LIKED_BY_USER_NC = "PostLiked"
COMMENT_LIKED_BY_USER_NC = "CommentLiked"
HOUSE_VISIT_SCHEDULED_NC = "HouseVisitScheduled"
FOLLOW_USER_NC = "FollowUser"
NEW_MESSAGE_NC = "NewMessage"
NEW_SCOUT_MESSAGE_NC = 'NewScoutMessage'

NotificationCategories = (
    (INSUFFICIENT_BALANCE_1_NC, INSUFFICIENT_BALANCE_1_NC),
    (INSUFFICIENT_BALANCE_2_NC, INSUFFICIENT_BALANCE_2_NC),
    (BATCH_ACCEPTED_NC, BATCH_ACCEPTED_NC),
    (BATCH_DELIVERED_NC, BATCH_DELIVERED_NC),
    (ORDER_DELIVERED_NC, ORDER_DELIVERED_NC),
    (CASHBACK_NC, CASHBACK_NC),
    (PROMOCODE_CASHBACK_NC, PROMOCODE_CASHBACK_NC),
    (TITLE_ASSIGNED_NC, TITLE_ASSIGNED_NC),
    (ALERT_NC, ALERT_NC),
    (ANNOUNCEMENT_NC, ANNOUNCEMENT_NC),
    (NEW_MESSAGE_NC, NEW_MESSAGE_NC),
    (PLACE_VISIT_NC, PLACE_VISIT_NC),
    (TENANT_PAYMENT_DUE_NC, TENANT_PAYMENT_DUE_NC),
    (TENANT_PAYMENT_SUCCESSFUL_NC, TENANT_PAYMENT_SUCCESSFUL_NC),
    (POST_LIKED_BY_USER_NC, POST_LIKED_BY_USER_NC),
    (COMMENT_LIKED_BY_USER_NC, COMMENT_LIKED_BY_USER_NC),
    (NEW_COMMENT_ON_POST_NC, NEW_COMMENT_ON_POST_NC),
    (HOUSE_VISIT_SCHEDULED_NC, HOUSE_VISIT_SCHEDULED_NC),
    (FOLLOW_USER_NC, FOLLOW_USER_NC),
    (NEW_SCOUT_MESSAGE_NC, NEW_SCOUT_MESSAGE_NC),
)


def get_notification_content_from_user_and_no_of_members(name, total_members, action_string):
    if total_members > 1:
        if total_members == 2:
            suffix_for_word_other = ''
        else:

            suffix_for_word_other = 's'
        return "{} and {} other{} {}".format(name, total_members - 1, suffix_for_word_other, action_string)
    else:
        return "{} {}".format(name, action_string)


def get_notification_image_upload_path(instance, filename):
    return "Notification/{}/{}".format(instance.category, filename)


def create_message_title_and_body(category, data=None):
    payload = {}
    display = True
    title = ""
    content = ""
    if category == INSUFFICIENT_BALANCE_1_NC:
        title = "Insufficient balance"
        content = "Insufficient balance in wallet. Please add money to continue delivery."

    elif category == INSUFFICIENT_BALANCE_2_NC:
        title = "Insufficient balance"
        content = "No upcoming delivery due to insufficient balance in wallet. Please add money to continue delivery."

    elif category == BATCH_ACCEPTED_NC:
        title = "Track order"
        content = "Your order is on the way!"
        payload = data

    elif category == BATCH_DELIVERED_NC:
        title = "Order delivered"
        content = "Your order was delivered! Please rate us for improvement of our service."
        payload = data

    elif category == ORDER_DELIVERED_NC:
        title = "Report delivery"
        content = "Thanks for the purchase! Have you received all items of your order?"
        payload = data

    elif category == CASHBACK_NC:
        title = "H-cash"
        content = "You have received H-Cash of amount ₹{}".format(data['amount'])

    elif category == PROMOCODE_CASHBACK_NC:
        title = "Successfully redeemed Promo Code {}".format(data['promo_code'])
        content = "You have received H-Cash of ₹{} in your wallet!".format(data['amount'])

    elif category == TITLE_ASSIGNED_NC:
        title = "Poll"
        content = 'You have received \"{}\" from {}'.format(data['title'], data['name'])

    elif category == PLACE_VISIT_NC:
        title = "Did you visit {}?".format(data['place_name'])
        content = 'Create a Check In for {} on Halanx!'.format(data['place_name'])

    elif category == NEW_MESSAGE_NC:
        title = "{} messaged you".format(data['sender_name'])
        content = data['msg'][:30]
        payload['sender_id'] = data['sender_id']
        display = False

    elif category == TENANT_PAYMENT_DUE_NC:
        title = "Please pay {}".format(data['description'])
        content = "Please pay ₹{} as {} before {}".format(data['amount'], data['description'], data['due_date'])

    elif category == TENANT_PAYMENT_SUCCESSFUL_NC:
        title = "Payment of {} was successful".format(data['description'])
        content = "Payment of {} of Rs.{} via {} was successful. Payment ID:-{}".format(data['description'],
                                                                                        data['amount'],
                                                                                        data['payment_gateway'],
                                                                                        data['payment_id'])

    elif category == ALERT_NC or category == ANNOUNCEMENT_NC:
        title = data['title']
        content = data['content']

    elif category == COMMENT_LIKED_BY_USER_NC:
        title = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                     total_members=data['sender_size'],
                                                                     action_string='liked your comment')

        content = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                       total_members=data['sender_size'],
                                                                       action_string='liked your comment')

    elif category == NEW_COMMENT_ON_POST_NC:
        title = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                     total_members=data['sender_size'],
                                                                     action_string='commented on your post')

        content = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                       total_members=data['sender_size'],
                                                                       action_string='commented on your post')

    elif category == POST_LIKED_BY_USER_NC:
        title = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                     total_members=data['sender_size'],
                                                                     action_string='liked your post')

        content = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                       total_members=data['sender_size'],
                                                                       action_string='liked your post')

    elif category == FOLLOW_USER_NC:
        title = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                     total_members=1,
                                                                     action_string='followed you')
        content = get_notification_content_from_user_and_no_of_members(name=data['sender_name'],
                                                                       total_members=1,
                                                                       action_string='followed you')

    elif category == NEW_SCOUT_MESSAGE_NC:
        title = data['scout_name'] + ' messaged You'
        content = data['message']

        display = False
    return title, content, payload, display


def send_customer_notification(customer, title, content, category, payload):
    notify_user(registration_id=customer.gcm_id,
                data_message={'data': json.dumps({'title': title, 'content': content,
                                                  'category': category, 'payload': payload})})
