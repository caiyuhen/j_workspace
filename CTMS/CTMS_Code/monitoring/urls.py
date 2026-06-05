from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonitoringVisitViewSet, ProtocolDeviationViewSet, QueryViewSet

router = DefaultRouter()
router.register(r'monitoring-visits', MonitoringVisitViewSet)
router.register(r'protocol-deviations', ProtocolDeviationViewSet)
router.register(r'queries', QueryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
