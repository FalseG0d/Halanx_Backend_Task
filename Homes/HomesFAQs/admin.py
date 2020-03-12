from django.contrib import admin

from Halanx.admin import halanxhomes_admin
from Homes.HomesFAQs.models import Topic, Question


@admin.register(Topic, site=halanxhomes_admin)
class TopicModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')

    class Meta:
        model = Topic


@admin.register(Question, site=halanxhomes_admin)
class QuestionModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'topic', 'created_on')
    prepopulated_fields = {'slug': ('text',)}
    list_filter = ('topic',)

    class Meta:
        model = Question
