from rest_framework import viewsets, permissions, exceptions
from django.utils import timezone
from .models import AdverseEvent
from .serializers import AdverseEventSerializer

class AdverseEventViewSet(viewsets.ModelViewSet):
    queryset = AdverseEvent.objects.all()
    serializer_class = AdverseEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        # Automatically set reporter
        serializer.save(reporter=user)
        
        # If serious, trigger PV notification (mock)
        if serializer.validated_data.get('is_serious') == 'YES':
            # In real system: send_email_to_pv(user, ae)
            pass

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'QA', 'PV', 'DM', 'STAT']:
            return AdverseEvent.objects.all()
        if user.role == 'PM':
            return AdverseEvent.objects.filter(subject__site__trial__project_manager=user)
        if user.role == 'CRA':
            return AdverseEvent.objects.filter(subject__site__assigned_cra=user)
        if user.role == 'INV':
            return AdverseEvent.objects.filter(subject__site__principal_investigator=user)
        return AdverseEvent.objects.none()
