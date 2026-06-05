from rest_framework import viewsets, permissions
from .models import MonitoringVisit, ProtocolDeviation, Query
from .serializers import MonitoringVisitSerializer, ProtocolDeviationSerializer, QuerySerializer

class MonitoringVisitViewSet(viewsets.ModelViewSet):
    queryset = MonitoringVisit.objects.all()
    serializer_class = MonitoringVisitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(monitor=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'PM', 'QA']:
            return MonitoringVisit.objects.all()
        if user.role == 'CRA':
            return MonitoringVisit.objects.filter(monitor=user)
        return MonitoringVisit.objects.none()

class ProtocolDeviationViewSet(viewsets.ModelViewSet):
    queryset = ProtocolDeviation.objects.all()
    serializer_class = ProtocolDeviationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'PM', 'QA', 'DM', 'PV']:
            return ProtocolDeviation.objects.all()
        if user.role == 'CRA':
            return ProtocolDeviation.objects.filter(site__assigned_cra=user) | ProtocolDeviation.objects.filter(reported_by=user)
        if user.role == 'INV':
            return ProtocolDeviation.objects.filter(site__principal_investigator=user)
        return ProtocolDeviation.objects.none()

class QueryViewSet(viewsets.ModelViewSet):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(raised_by=self.request.user)

    def perform_update(self, serializer):
        # If answering, set answered_by
        if 'answer_text' in serializer.validated_data and serializer.validated_data['answer_text']:
             serializer.save(answered_by=self.request.user)
        else:
             serializer.save()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'PM', 'QA', 'DM', 'PV']:
            return Query.objects.all()
        if user.role == 'CRA':
             return Query.objects.filter(visit__subject__site__assigned_cra=user)
        if user.role == 'INV':
             return Query.objects.filter(visit__subject__site__principal_investigator=user)
        return Query.objects.none()
