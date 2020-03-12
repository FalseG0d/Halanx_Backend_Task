from django.conf.urls import url

from Homes.Tenants.api import views


urlpatterns = (
    url(r'^detail/$', views.TenantRetrieveUpdateView.as_view()),
    url(r'^documents/$', views.TenantDocumentListCreateView.as_view()),
    url(r'^documents/(?P<pk>[0-9]+)/$', views.TenantDocumentRetrieveDestroyView.as_view()),
    url(r'^payments/$', views.TenantPaymentListView.as_view()),
    url(r'^payments/(?P<pk>[0-9]+)/$', views.TenantPaymentRetrieveUpdateView.as_view()),
    url(r'^payments/(?P<pk>[0-9]+)/cash_collection_time_slots/$',
        views.TenantPaymentCashCollectionTimeSlotsRetrieveView.as_view()),
    url(r'^payments/batch/$', views.TenantPaymentBatchUpdateView.as_view()),
    url(r'^refer_and_earn/$', views.TenantReferAndEarnView.as_view()),
    url(r'^fav_houses/$', views.TenantFavoriteHousesListView.as_view()),

    url(r'^request_moveout/$', views.TenantMoveOutRequestCreateView.as_view()),
    url(r'^requirements/$', views.TenantRequirementCreateView.as_view()),

    # Owner App urls
    url(r'^$', views.TenantListView.as_view()),
    url(r'^(?P<pk>[0-9]+)/$', views.TenantRetrieveView.as_view()),
    url(r'^create/$', views.create_tenant_view),

    url(r'^latecheckins/$', views.TenantLateCheckinListCreateView.as_view()),
    url(r'^latecheckins/(?P<pk>[0-9]+)/$', views.TenantLateCheckinDestroyView.as_view()),

    url(r'^meals/$', views.TenantMealListCreateView.as_view()),
    url(r'^meals/accept/', views.tenant_accept_meal),
    url(r'bills/$', views.TenantBillListView.as_view()),

    url(r'timeline/$', views.TenantTimeLineView.as_view()),

)
