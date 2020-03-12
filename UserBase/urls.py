from django.conf.urls import url

from UserBase import views

urlpatterns = (
    url(r'^register/$', views.register),
    url(r'^social/register/$', views.register_social),
    url(r'^get_otp/(?P<phone_no>\w+)/$', views.generate_otp),
    url(r'^get_email_otp/$', views.generate_email_otp),

    url(r'^login_otp/$', views.login_with_otp),

    url(r'^verify_otp/$', views.verify_otp),
    url(r'^verify_email_otp/$', views.verify_email_otp),
    url(r'^social/link/$', views.link_social_account_with_already_registered_phone_no),


    url(r'^exists/(?P<phone_no>\w+)/$', views.user_exists),
    url(r'^logout/$', views.user_logout),
    url(r'^email/verify/$', views.verify_email),

    url(r'^detail/$', views.user_detail),
    url(r'^(?P<pk>\d+)/detail/$', views.user_id),
    url(r'^refer_and_earn/$', views.user_refer_and_earn),
    url(r'^location/$', views.user_location),

    url(r'^(?P<pk>\d+)/album/$', views.user_album),
    url(r'^pictures/$', views.user_picture_list),
    url(r'^pictures/(?P<pk>\d+)/$', views.user_picture),

    url(r'^(?P<pk>\d+)/follow/$', views.user_follow_toggle),
    url(r'^followers/$', views.my_followers_list),
    url(r'^following/$', views.my_following_list),
    url(r'^(?P<pk>\d+)/followers/$', views.user_followers_list),
    url(r'^(?P<pk>\d+)/following/$', views.user_following_list),

    url(r'^fav_item_toggle/(?P<pk>\d+)/$', views.user_favorite_items_toggle),
    url(r'^fav_items/$', views.user_favorite_items_list),

    url(r'^fav_places/$', views.user_favorite_places_list),

    url(r'^rate_shopper/$', views.user_rate_shopper),
    url(r'^add_balance/$', views.user_add_balance),
    url(r'^report_spam/(?P<pk>\d+)/$', views.user_report_spam),
    url(r'^filter/$', views.user_filter),

    url(r'^interests/list/$', views.interests_list),
    url(r'^interests/$', views.user_interests),

    url(r'^work/$', views.user_work_list),
    url(r'^work/(?P<pk>\d+)/$', views.user_work),
    url(r'^education/$', views.user_education_list),
    url(r'^education/(?P<pk>\d+)/$', views.user_education),
    url(r'^contacts/$', views.user_contact_list),
    url(r'^contacts/halanx/$', views.my_halanx_contacts_list),

    url(r'^analytics/$', views.user_analytics),
    url(r'^analytics/sms/$', views.user_analytics_sms),
    url(r'^analytics/notification/$', views.user_analytics_notification, name='user_analytics_notification'),
    url(r'^analytics/email/$', views.user_analytics_email),
    url(r'^ajax_filter/$', views.user_ajax_filter),

    url(r'^fbsharer/generate/$', views.user_fb_template_generator),
    url(r'^fbsharer/(?P<uid>\d+)/$', views.fbsharer),

    url(r'^detail/(?P<pk>\d+)/$', views.user_id),  # remove later
    url(r'^album/(?P<pk>\d+)/$', views.user_album),  # remove later
    url(r'^follow/(?P<pk>\d+)/$', views.user_follow_toggle),  # remove later


)
