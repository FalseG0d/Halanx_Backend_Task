from django.conf.urls import url
from Homes.OperationManagers.api import views

urlpatterns = (
    url(r'service_requests/page_data/$', views.ServiceRequestPageDataView.as_view()),
    url(r'^service_requests/$', views.ServiceRequestListView.as_view()),
    url(r'^service_requests/(?P<pk>[0-9]+)/$', views.ServiceRequestRetrieveUpdateView.as_view()),

    url(r'staff_members/$', views.StaffMemberListCreateView.as_view()),
    url(r'staff_members/(?P<pk>[0-9]+)/$', views.StaffMemberRetrieveUpdateView.as_view()),

    url(r'sms_houses_list/$', views.MultipleHouseDetailsToTenantSMSView.as_view()),

    url(r'payments/$', views.PaymentsListView.as_view()),
    url(r'search/$', views.search_view),
    url(r'metrics/$', views.MetricDashboardAPIView.as_view()),
)
