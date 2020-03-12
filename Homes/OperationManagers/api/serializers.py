from rest_framework import serializers

from Homes.HomeServices.models import ServiceRequest


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = '__all__'
