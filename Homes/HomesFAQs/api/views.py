from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from Homes.HomesFAQs.models import Question, Topic
from Homes.HomesFAQs.api.serializers import TopicListSerializer, QuestionSerializer


class TopicListView(ListAPIView):
    serializer_class = TopicListSerializer
    queryset = Topic.objects.all()

    @method_decorator(cache_page(60 * 60))
    def dispatch(self, *args, **kwargs):
        return super(TopicListView, self).dispatch(*args, **kwargs)


class TopicDetailView(ListAPIView):
    lookup_field = 'slug'
    serializer_class = QuestionSerializer

    def get_queryset(self):
        slug = self.kwargs['slug']
        queryset = Question.objects.filter(active=True, topic__slug=slug)
        return queryset

    @method_decorator(cache_page(60 * 60))
    def dispatch(self, *args, **kwargs):
        return super(TopicDetailView, self).dispatch(*args, **kwargs)


class QuestionDetailView(RetrieveAPIView):
    lookup_field = 'slug'
    serializer_class = QuestionSerializer

    def get_queryset(self):
        topic = self.kwargs['topic__slug']
        slug = self.kwargs['slug']
        queryset = Question.objects.filter(active=True, topic__slug=topic, slug=slug)
        return queryset

    @method_decorator(cache_page(60 * 60))
    def dispatch(self, *args, **kwargs):
        return super(QuestionDetailView, self).dispatch(*args, **kwargs)
