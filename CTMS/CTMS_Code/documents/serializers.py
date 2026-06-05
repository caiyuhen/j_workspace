from rest_framework import serializers
from .models import Document
from users.serializers import UserSerializer

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserSerializer(source='uploaded_by', read_only=True)
    locked_by_details = UserSerializer(source='locked_by', read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'locked_by', 'locked_at']
