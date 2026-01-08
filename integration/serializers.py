# integration/serializers.py

from rest_framework import serializers
from .models import MoySkladProduct, MoySkladCategory, MoySkladBrand, MoySkladOrder, SyncLog


class MoySkladProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoySkladProduct
        fields = '__all__'


class MoySkladCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MoySkladCategory
        fields = '__all__'


class MoySkladBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoySkladBrand
        fields = '__all__'


class MoySkladOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoySkladOrder
        fields = '__all__'


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = '__all__'