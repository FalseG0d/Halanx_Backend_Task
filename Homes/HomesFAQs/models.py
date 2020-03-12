from django.db import models
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify

User = get_user_model()


class Topic(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        ordering = ('name',)

    def __str__(self):
        return self.name


class Question(models.Model):
    topic = models.ForeignKey(Topic, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    answer = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=False, auto_now=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='homes_faqs')

    class Meta:
        verbose_name = "Frequent asked question"
        verbose_name_plural = "Frequently asked questions"
        ordering = ('created_on',)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        # Create a unique slug, if needed.
        if not self.slug:
            suffix = 0
            potential = base = slugify(self.text[:90])
            while not self.slug:
                if suffix:
                    potential = "%s-%s" % (base, suffix)
                if not Question.objects.filter(slug=potential).exists():
                    self.slug = potential
                # We hit a conflicting slug; increment the suffix and try again.
                suffix += 1

        super(Question, self).save(*args, **kwargs)
