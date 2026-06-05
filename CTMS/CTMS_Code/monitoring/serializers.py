from rest_framework import serializers
from .models import MonitoringVisit, ProtocolDeviation, Query
from users.serializers import UserSerializer
from trials.serializers import SiteSerializer

class MonitoringVisitSerializer(serializers.ModelSerializer):
    monitor_details = UserSerializer(source='monitor', read_only=True)
    site_details = SiteSerializer(source='site', read_only=True)

    class Meta:
        model = MonitoringVisit
        fields = '__all__'
        read_only_fields = ['monitor']

class ProtocolDeviationSerializer(serializers.ModelSerializer):
    reported_by_details = UserSerializer(source='reported_by', read_only=True)
    site_details = SiteSerializer(source='site', read_only=True)

    class Meta:
        model = ProtocolDeviation
        fields = '__all__'
        read_only_fields = ['reported_by']

class QuerySerializer(serializers.ModelSerializer):
    raised_by_details = UserSerializer(source='raised_by', read_only=True)
    answered_by_details = UserSerializer(source='answered_by', read_only=True)
    
    class Meta:
        model = Query
        fields = '__all__'
        read_only_fields = ['raised_by', 'answered_by']
