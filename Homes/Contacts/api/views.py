from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from Homes.Contacts.api.serializers import EnquirySerializer
from decouple import config
import requests


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def verify_captcha(request):
    if request.data.get('nocaptcha'):
        return True
    captcha = request.data.get('captcha')
    ip = get_client_ip(request)
    data = {
        'secret': config('CAPTCHA_SECRET_KEY'),
        'response': captcha,
        'remoteip': ip
    }
    url = "https://www.google.com/recaptcha/api/siteverify"
    res = requests.post(url, data=data).json()
    return res.get('success')


class EnquiryCreateView(CreateAPIView):
    serializer_class = EnquirySerializer

    def create(self, request, *args, **kwargs):
        if verify_captcha(request):
            serializer = EnquirySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
            return Response(serializer.data)
        else:
            return Response({"error": "Invalid captcha"}, status=status.HTTP_403_FORBIDDEN)
