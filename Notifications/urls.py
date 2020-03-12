from django.conf.urls import url

from Notifications.api import views

urlpatterns = [
    url(r'^user/$', views.user_notifications),
]
