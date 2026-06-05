from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Default is_online to True if no file is provided? 
        # For now, let frontend set is_online=True explicitly if creating online doc.
        serializer.save(uploaded_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Document.objects.none()

        if user.is_staff or user.role in ['ADMIN', 'QA', 'PV', 'PM']:
            return Document.objects.all()
        if user.role == 'CRA':
            # CRA can see docs for their assigned sites
            return Document.objects.filter(site__assigned_cra=user) | Document.objects.filter(uploaded_by=user)
        if user.role == 'INV':
            # INV can see docs for their site
            return Document.objects.filter(site__principal_investigator=user) | Document.objects.filter(uploaded_by=user)
        return Document.objects.filter(uploaded_by=user)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        document = self.get_object()
        user = request.user
        
        if document.locked_by and document.locked_by != user:
            return Response(
                {'error': f'Document is currently locked by {document.locked_by.username}'},
                status=status.HTTP_409_CONFLICT
            )
        
        document.locked_by = user
        document.locked_at = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        document = self.get_object()
        user = request.user
        
        # Only the locker or an admin can unlock
        if document.locked_by and document.locked_by != user and not user.is_staff:
             return Response(
                {'error': 'You cannot unlock a document locked by someone else'},
                status=status.HTTP_403_FORBIDDEN
            )

        document.locked_by = None
        document.locked_at = None
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def save_content(self, request, pk=None):
        document = self.get_object()
        user = request.user
        
        # Must be locked by user to save
        if document.locked_by != user:
             return Response(
                {'error': 'You must lock the document before editing'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        content = request.data.get('content')
        if content is not None:
            document.content = content
            document.save()
            
        serializer = self.get_serializer(document)
        return Response(serializer.data)
