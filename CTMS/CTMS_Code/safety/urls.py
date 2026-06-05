from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdverseEventViewSet

router = DefaultRouter()
router.register(r'adverse-events', AdverseEventViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
