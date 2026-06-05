from rest_framework import viewsets, permissions, exceptions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Subject, Visit, Specimen, SignatureLog
from .serializers import SubjectSerializer, VisitSerializer, SpecimenSerializer
from trials.models import Site

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'QA', 'PV', 'DM', 'STAT']:
            return Subject.objects.all()
        if user.role == 'PM':
            return Subject.objects.filter(site__trial__project_manager=user)
        if user.role == 'CRA':
            return Subject.objects.filter(site__assigned_cra=user)
        if user.role == 'INV':
            return Subject.objects.filter(site__principal_investigator=user)
        return Subject.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        site = serializer.validated_data.get('site')
        
        # Investigator can only create subjects for their site
        if user.role == 'INV':
            if site.principal_investigator != user:
                raise exceptions.PermissionDenied("You can only add subjects to your own site.")
        
        # CRA/PM check logic could be added here
        serializer.save()

class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['subject', 'status', 'data_status']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'QA', 'PV', 'DM', 'STAT']:
            return Visit.objects.all()
        if user.role == 'PM':
            return Visit.objects.filter(subject__site__trial__project_manager=user)
        if user.role == 'CRA':
            return Visit.objects.filter(subject__site__assigned_cra=user)
        if user.role == 'INV':
            return Visit.objects.filter(subject__site__principal_investigator=user)
        return Visit.objects.none()

    @action(detail=True, methods=['post'], url_path='sign')
    def sign_visit(self, request, pk=None):
        visit = self.get_object()
        password = request.data.get('password')
        reason = request.data.get('reason', 'Electronic Signature')
        
        if not password:
            return Response({"detail": "Password required for electronic signature"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify password
        user = request.user
        if not user.check_password(password):
             return Response({"detail": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
             
        # Perform signature
        visit.data_status = 'SIGNED'
        # visit.is_monitored = True # SDV is separate
        visit.save()
        
        # Log signature
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        SignatureLog.objects.create(
            visit=visit,
            signer=user,
            reason=reason,
            ip_address=ip
        )
        
        return Response(VisitSerializer(visit).data)

    @action(detail=True, methods=['post'], url_path='sdv')
    def sdv_visit(self, request, pk=None):
        visit = self.get_object()
        user = request.user
        
        # Only CRA or PM or ADMIN can perform SDV
        if user.role not in ['CRA', 'PM', 'ADMIN'] and not user.is_staff:
             return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
             
        visit.is_monitored = True
        visit.data_status = 'VERIFIED'
        visit.monitored_by = user
        visit.monitored_at = timezone.now()
        visit.save()
        
        return Response(VisitSerializer(visit).data)

class SpecimenViewSet(viewsets.ModelViewSet):
    queryset = Specimen.objects.all()
    serializer_class = SpecimenSerializer
    permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['subject', 'specimen_type']

    def get_queryset(self):
        user = self.request.user
        queryset = Specimen.objects.all()
        
        if user.is_staff or user.role in ['ADMIN', 'QA', 'PV', 'DM', 'STAT']:
            pass
        elif user.role == 'PM':
            queryset = queryset.filter(subject__site__trial__project_manager=user)
        elif user.role == 'CRA':
            queryset = queryset.filter(subject__site__assigned_cra=user)
        elif user.role == 'INV':
            queryset = queryset.filter(subject__site__principal_investigator=user)
        else:
            return Specimen.objects.none()

        # Manual Filters
        subject_id = self.request.query_params.get('subject')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
            
        specimen_type = self.request.query_params.get('specimen_type')
        if specimen_type:
            queryset = queryset.filter(specimen_type=specimen_type)
            
        return queryset
