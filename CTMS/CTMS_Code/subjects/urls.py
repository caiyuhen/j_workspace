from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, VisitViewSet, SpecimenViewSet

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'visits', VisitViewSet)
router.register(r'specimens', SpecimenViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
