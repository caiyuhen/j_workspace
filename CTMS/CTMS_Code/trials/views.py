from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Trial, Site, InvestigationalProduct
from .serializers import TrialSerializer, SiteSerializer, InvestigationalProductSerializer

class TrialViewSet(viewsets.ModelViewSet):
    queryset = Trial.objects.all()
    serializer_class = TrialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(project_manager=user)

    def perform_destroy(self, instance):
        user = self.request.user
        # Only ADMIN or the Project Manager of the trial can delete it
        if not (user.is_staff or user.role in ['ADMIN', 'QA'] or (user.role == 'PM' and instance.project_manager == user)):
             raise PermissionDenied("You do not have permission to delete this trial.")
        instance.delete()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'QA', 'PV']:
            return Trial.objects.all()
        if user.role == 'PM':
            return Trial.objects.filter(project_manager=user)
        if user.role == 'CRA':
            # return trials where CRA is assigned to at least one site
            return Trial.objects.filter(sites__assigned_cra=user).distinct()
        if user.role == 'INV':
            return Trial.objects.filter(sites__principal_investigator=user).distinct()
        return Trial.objects.none()

class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role in ['ADMIN', 'QA', 'PV']:
            return Site.objects.all()
        if user.role == 'PM':
            return Site.objects.filter(trial__project_manager=user)
        if user.role == 'CRA':
            return Site.objects.filter(assigned_cra=user)
        if user.role == 'INV':
            return Site.objects.filter(principal_investigator=user)
        return Site.objects.none()

class InvestigationalProductViewSet(viewsets.ModelViewSet):
    serializer_class = InvestigationalProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = InvestigationalProduct.objects.all()

        # RBAC
        if not (user.is_staff or user.role in ['ADMIN', 'QA', 'PV']):
             if user.role == 'PM':
                 queryset = queryset.filter(trial__project_manager=user)
             elif user.role == 'CRA':
                 queryset = queryset.filter(trial__sites__assigned_cra=user).distinct()
             elif user.role == 'INV':
                 queryset = queryset.filter(trial__sites__principal_investigator=user).distinct()
             else:
                 return InvestigationalProduct.objects.none()

        # Filters
        trial_id = self.request.query_params.get('trial')
        if trial_id:
            queryset = queryset.filter(trial_id=trial_id)
            
        product_type = self.request.query_params.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
            
        return queryset
