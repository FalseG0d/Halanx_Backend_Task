from django.conf.urls import url

import Homes.Owners.api.views
from Homes.Houses.api import views

urlpatterns = (
    url(r'^spacetypes/$', views.get_space_types),

    url(r'^$', views.HouseListView.as_view()),
    url(r'^apply/$', views.HouseApplicationCreateView.as_view()),
    url(r'^(?P<pk>[0-9]+)/$', views.HouseRetrieveView.as_view()),
    url(r'^(?P<pk>[0-9]+)/visits/timeslots/$', views.HouseVisitTimeSlotView.as_view()),
    url(r'^(?P<pk>[0-9]+)/favorite/$', views.TenantFavoritePlaceToggleView.as_view()),
    url(r'^(?P<pk>[0-9]+)/share/$', views.share_house),
    url(r'^visits/$', views.HouseVisitListCreateView.as_view()),
    url(r'^visits/(?P<pk>[0-9]+)/$', views.HouseVisitRetrieveUpdateDeleteAPIView.as_view()),

    url(r'^slug/(?P<slug>[\w\-]+)/$', views.HouseSearchSlugRetrieveView.as_view()),

    url(r'^locations/popular/', views.PopularLocationListView.as_view()),
    url(r'^basic_amenities/$', views.AmenityListView.as_view()),

    # Below url is for just testing purpose to save post and get data
    url(r'^data/sample/$', views.save_request_data),

    # Spaces
    url(r'^spaces/$', Homes.Owners.api.views.HouseSpaceListCreateView.as_view()),
    url(r'^spaces/(?P<pk>[0-9]+)/$', Homes.Owners.api.views.HouseSpaceRetrieveUpdateDestroyView.as_view()),

    # Vendors
    url(r'^occupations/$', views.OccupationListView.as_view()),

    # Bills
    url(r'^bills/categories/$', views.BillCategoryListView.as_view()),

)
