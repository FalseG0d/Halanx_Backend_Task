from rest_framework import serializers

from Common.models import PaymentCategory


class PaymentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCategory
        fields = '__all__'
