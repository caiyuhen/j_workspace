from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="CTMS API",
      default_version='v1',
      description="API for Clinical Trial Management System",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@ctms.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from core.views import DashboardStatsView, AuditLogViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/dashboard/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("api/v1/audit-logs/", AuditLogViewSet.as_view({'get': 'list'}), name="audit-logs"),
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("trials.urls")),
    path("api/v1/", include("subjects.urls")),
    path("api/v1/", include("safety.urls")),
    path("api/v1/", include("documents.urls")),
    path("api/v1/", include("monitoring.urls")),
    path("api-auth/", include("rest_framework.urls")),  # For browsable API login
    
    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
