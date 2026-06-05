from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrialViewSet, SiteViewSet, InvestigationalProductViewSet

router = DefaultRouter()
router.register(r'trials', TrialViewSet)
router.register(r'sites', SiteViewSet)
router.register(r'products', InvestigationalProductViewSet, basename='investigationalproduct')

urlpatterns = [
    path('', include(router.urls)),
]
