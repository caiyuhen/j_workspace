from rest_framework import serializers
from .models import Subject, Visit, Specimen
from trials.serializers import SiteSerializer
from users.serializers import UserSerializer

class VisitSerializer(serializers.ModelSerializer):
    monitored_by_details = UserSerializer(source='monitored_by', read_only=True)

    class Meta:
        model = Visit
        fields = '__all__'

class SpecimenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specimen
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    visits = VisitSerializer(many=True, read_only=True)
    site_details = SiteSerializer(source='site', read_only=True)

    class Meta:
        model = Subject
        fields = '__all__'
