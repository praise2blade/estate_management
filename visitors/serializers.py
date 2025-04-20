from rest_framework import serializers
from .models import Visitor, VisitRequest

class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = '__all__'

class VisitRequestSerializer(serializers.ModelSerializer):
    visitor = VisitorSerializer()

    class Meta:
        model = VisitRequest
        fields = '__all__'
