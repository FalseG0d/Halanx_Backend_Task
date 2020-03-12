from django.conf.urls import url
from Homes.HomeServices.api import views

urlpatterns = (
    url(r'^categories/$', views.MajorServiceCategoryListView.as_view()),

    url(r'^requests/$', views.ServiceRequestListCreateView.as_view()),
    url(r'^requests/(?P<pk>[0-9]+)/$', views.ServiceRequestRetrieveUpdateView.as_view()),
    url(r'^requests/(?P<pk>[0-9]+)/image/upload/$', views.ServiceRequestImageCreateView.as_view()),
)
