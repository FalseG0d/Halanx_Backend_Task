from django.conf.urls import url

from Homes.AreaManagers import views

urlpatterns = (
    url(r'^$', views.home_page, name='home_page'),
    url(r'^login/$', views.login_view, name='login_page'),
    url(r'^logout/$', views.logout_view, name='area_manager_logout'),

    # basic tenant views
    url(r'^tenants/$', views.tenants_page, name='tenants_page'),
    url(r'^tenants/new/$', views.create_new_tenant_view, name='create_new_tenant_view'),
    url(r'^tenants/(?P<pk>\d+)/profile/$', views.tenant_profile_edit_view, name='tenant_profile_edit_view'),
    url(r'^tenants/(?P<pk>\d+)/bookings/$', views.tenant_bookings_page, name='tenant_bookings_page'),

    # tenant onboarding
    url(r'^tenants/(?P<pk>\d+)/onboard/$', views.onboard_page, name='onboard_page'),
    url(r'^tenants/onboard/create-booking/$', views.create_existing_tenant_booking_view,
        name='existing_tenant_booking_view'),

    # tenant move-in
    url(r'^tenants/(?P<pk>\d+)/movein/$', views.move_in_page, name='move_in_page'),
    url(r'^bookings/(?P<pk>\d+)/movein/confirm/$', views.move_in_confirmation_view, name='move_in_confirm_view'),
    url(r'^bookings/(?P<pk>\d+)/movein/agreement/$', views.move_in_agreement_view, name='move_in_agreement_view'),

    # tenant move-out
    url(r'^tenants/(?P<pk>\d+)/moveout/$', views.move_out_page, name='move_out_page'),
    url(r'^bookings/(?P<pk>\d+)/moveout/confirm/$', views.move_out_confirmation_view, name='move_out_confirm_view'),

    # tenant monthly rents
    url(r'^tenants/(?P<pk>\d+)/monthly-rents/$', views.monthly_rents_page, name='monthly_rents_page'),
    url(r'^monthly-rents/create/$', views.create_monthly_rent_view, name='monthly_rent_create_view'),
    url(r'^monthly-rents/delete/$', views.delete_monthly_rent_view, name='monthly_rent_delete_view'),

    # tenant payments
    url(r'^tenants/(?P<pk>\d+)/payments/$', views.tenant_payments_page, name='tenant_payments_page'),
    url(r'^payments/(?P<pk>\d+)/edit/$', views.tenant_payment_edit_view, name='tenant_payment_edit_view'),

    # area manager cash collection
    url(r'cash-collect/$', views.cash_collection_page, name='cash_collection_page'),
    url(r'cash-collect/(?P<pk>\d+)/confirm/$', views.cash_collection_confirmation_view,
        name='cash_collect_confirm_view'),

    # area manager cash deposit
    url(r'cash-deposit/$', views.cash_deposit_page, name='cash_deposit_page'),

    # area manager house visits
    url(r'house-visits/$', views.house_visits_page, name='house_visits_page'),

    # house manage views
    url(r'houses/$', views.house_index_page, name='house_edit_index_page'),
    url(r'houses/(?P<pk>\d+)/$', views.house_main_page, name='house_edit_main_page'),
    url(r'houses/(?P<pk>\d+)/spaces/create/$', views.create_house_spaces_view, name='house_spaces_create_view'),
    url(r'houses/(?P<pk>\d+)/spaces/delete/$', views.delete_house_space_view, name='house_space_delete_view'),
    url(r'houses/(?P<pk>\d+)/spaces/update/$', views.update_house_subtype_spaces_view,
        name='house_subtype_spaces_update_view'),
    url(r'houses/(?P<pk>\d+)/bookings/$', views.house_bookings_page, name='house_bookings_page'),
    url(r'houses/spaces/update', views.multiple_space_update_view, name='space_update_view'),

    # sms utility view
    url(r'send-sms/$', views.send_sms_view, name='send_sms_view'),
)
