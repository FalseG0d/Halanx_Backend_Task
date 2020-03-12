from rest_framework import serializers
from Homes.HomesFAQs.models import Question, Topic
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")


class TopicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    topic = TopicListSerializer(read_only=True)

    class Meta:
        model = Question
        fields = '__all__'


class QuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('text', 'slug', 'created_by', 'created_on')
