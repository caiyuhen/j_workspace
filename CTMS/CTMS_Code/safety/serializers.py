from rest_framework import serializers
from .models import AdverseEvent
from subjects.serializers import SubjectSerializer
from users.serializers import UserSerializer

class AdverseEventSerializer(serializers.ModelSerializer):
    subject_details = SubjectSerializer(source='subject', read_only=True)
    reporter_details = UserSerializer(source='reporter', read_only=True)

    class Meta:
        model = AdverseEvent
        fields = '__all__'
        read_only_fields = ['reporter', 'reported_to_pv_at', 'reported_to_regulatory_at']
