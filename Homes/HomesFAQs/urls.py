from django.conf.urls import url
from Homes.HomesFAQs.api import views

urlpatterns = (
    url(r'^$', views.TopicListView.as_view()),
    url(r'^(?P<slug>[-\w]+)/$', views.TopicDetailView.as_view()),
    url(r'^(?P<topic__slug>[-\w]+)/(?P<slug>[-\w]+)/$', views.QuestionDetailView.as_view()),
)
