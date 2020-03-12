from django.conf.urls import url
from Homes.Contacts.api import views

urlpatterns = (
    url(r'^submit/$', views.EnquiryCreateView.as_view()),
)
