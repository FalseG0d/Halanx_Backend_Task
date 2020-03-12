from django.conf.urls import url
from Homes.Owners.api import views

urlpatterns = (
    url(r'^$', views.OwnerRetrieveUpdateView.as_view()),
    url(r'^register/$', views.OwnerCreateView.as_view()),
    url(r'^login_otp/$', views.login_with_otp),
    url(r'^exists/(?P<phone_no>\w+)/$', views.owner_exists),

    # Owner Houses List, Create, Retrieve, Update, Destroy
    url(r'^houses/$', views.OwnerHouseListCreateView.as_view()),
    url(r'^houses/(?P<pk>[0-9]+)/pictures/$', views.OwnerHousePictureListCreateView.as_view()),
    url(r'^houses/(?P<pk>[0-9]+)/$', views.OwnerHouseRetrieveUpdateDestroyView.as_view()),

    url(r'^houses/(?P<pk>[0-9]+)/spaces/$', views.get_house_spaces_detail),
    url(r'^houses/(?P<pk>[0-9]+)/rent/$', views.get_house_rent_detail),
    url(r'^houses/(?P<pk>[0-9]+)/tenants/$', views.get_house_tenants_detail),
    url(r'^houses/(?P<pk>[0-9]+)/furnish-items/$', views.OwnerHouseExistingFacilityListView.as_view()),

    url(r'^wallet/summary/$', views.OwnerWalletDetailView.as_view()),
    url(r'^wallet/statement/$', views.OwnerPaymentListView.as_view()),
    url(r'^wallet/withdrawal-requests/$', views.WithdrawalRequestListCreateView.as_view()),

    url(r'^notifications/$', views.OwnerNotificationListView.as_view()),
    url(r'^documents/$', views.OwnerDocumentListCreateView.as_view()),
    url(r'^documents/(?P<pk>[0-9]+)/$', views.OwnerDocumentRetrieveDestroyView.as_view()),
    url(r'^refer_and_earn/$', views.OwnerReferAndEarnView.as_view()),
    url(r'^listing/', views.OwnerListingCreateView.as_view()),
    url(r'houses/visits/', views.HouseVisitListView.as_view()),

    # Owner Team Members
    url(r'^team/members/$', views.TeamMemberListCreateView.as_view()),
    url(r'^team/members/(?P<pk>[0-9]+)/$', views.TeamMemberRetrieveUpdateDestroyView.as_view()),

    # Vendors
    url(r'^vendors/$', views.VendorListCreateView.as_view()),
    url(r'^vendors/(?P<pk>[0-9]+)/$', views.VendorRetrieveUpdateDestroyView.as_view()),

    # Bills
    url(r'^create_tenant_group/$', views.create_tenant_group_view),
    url(r'^(?P<pk>[0-9]+)/bills/$', views.HouseBillListCreateView.as_view()),

    url(r'^bills/$', views.BillListView.as_view()),
    url(r'^bills/(?P<pk>[0-9]+)/split/create/$', views.create_bill_split),

)
