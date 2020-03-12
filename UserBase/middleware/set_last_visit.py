from django.utils import timezone

from UserBase.models import Customer


class SetLastVisitMiddleware(object):
    @staticmethod
    def process_response(request, response):
        try:
            Customer.objects.filter(user=request.user).update(last_visit=timezone.now())
        except (AttributeError, TypeError):
            pass
        return response
