from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import calendar
from django.apps import apps

from trials.models import Trial, Site
from subjects.models import Subject, Visit
from safety.models import AdverseEvent
from documents.models import Document
from monitoring.models import Query, MonitoringVisit, ProtocolDeviation

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class AuditLogViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        model_name = request.query_params.get('model', 'Trial')
        app_label_map = {
            'Trial': 'trials',
            'Site': 'trials',
            'InvestigationalProduct': 'trials',
            'Subject': 'subjects',
            'Visit': 'subjects',
            'Specimen': 'subjects',
            'AdverseEvent': 'safety',
            'Document': 'documents',
            'User': 'users',
            'Query': 'monitoring',
            'MonitoringVisit': 'monitoring',
            'ProtocolDeviation': 'monitoring',
        }
        
        if model_name not in app_label_map:
             return Response({"error": "Invalid model name"}, status=400)
             
        try:
            Model = apps.get_model(app_label_map[model_name], model_name)
            if not hasattr(Model, 'history'):
                 return Response({"error": "Model has no history"}, status=400)
            
            queryset = Model.history.all().order_by('-history_date')
            
            # Filter by object_id if provided
            object_id = request.query_params.get('object_id')
            if object_id:
                queryset = queryset.filter(id=object_id)
            
            # Pagination
            paginator = StandardResultsSetPagination()
            page = paginator.paginate_queryset(queryset, request)
            
            # Serialize
            data = []
            history_type_map = {'+': 'Created', '~': 'Updated', '-': 'Deleted'}
            
            for record in page:
                user_str = "System"
                if record.history_user:
                    user_str = record.history_user.username
                
                changes = []
                if record.prev_record:
                    delta = record.diff_against(record.prev_record)
                    for change in delta.changes:
                        changes.append({
                            "field": change.field,
                            "old": str(change.old),
                            "new": str(change.new)
                        })
                
                # For Created records, we can list all fields as new
                if record.history_type == '+':
                     changes = [{"field": "all", "old": "", "new": "Record Created"}]
                
                data.append({
                    "id": record.history_id,
                    "date": record.history_date,
                    "user": user_str,
                    "action": history_type_map.get(record.history_type, record.history_type),
                    "object_repr": str(record.instance) if record.instance else str(record),
                    "changes": changes,
                    "ip_address": "N/A" # simple_history doesn't track IP by default unless configured
                })
                
            return paginator.get_paginated_response(data)

        except LookupError:
             return Response({"error": "Model not found"}, status=400)

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _request):
        # 1. Trial Stats
        total_trials = Trial.objects.count()
        active_trials = Trial.objects.filter(status='ACTIVE').count()
        
        # 2. Subject Stats
        total_subjects = Subject.objects.count()
        active_subjects = Subject.objects.filter(status__in=['ACTIVE', 'ENROLLED']).count()
        enrolled_subjects = Subject.objects.filter(status='ENROLLED').count()
        
        # 3. Safety Stats
        pending_saes = AdverseEvent.objects.filter(is_serious='YES', outcome__in=['NOT_RECOVERED', 'UNKNOWN']).count()
        
        # 4. Site Stats
        total_sites = Site.objects.count()
        active_sites = Site.objects.filter(status='ACTIVE').count()

        # 5. Recruitment Trend (Last 6 months based on informed_consent_date)
        today = timezone.now().date()
        six_months_ago = today - timedelta(days=180)
        
        current_year = today.year
        current_month = today.month
        
        trend_data = []
        for i in range(5, -1, -1):
             m = current_month - i
             y = current_year
             if m <= 0:
                 m += 12
                 y -= 1
             
             month_name = calendar.month_name[m][:3]
             trend_data.append({
                "name": month_name,
                "month_idx": m,
                "year": y,
                "subjects": 0
             })
            
        # Query
        recruitment_qs = (
            Subject.objects.filter(informed_consent_date__gte=six_months_ago)
            .values('informed_consent_date__month', 'informed_consent_date__year')
            .annotate(count=Count('id'))
        )
        
        # Map query results to buckets
        for item in recruitment_qs:
            m = item['informed_consent_date__month']
            y = item['informed_consent_date__year']
            c = item['count']
            
            for bucket in trend_data:
                if bucket['month_idx'] == m and bucket['year'] == y:
                    bucket['subjects'] = c
                    break
        
        # Clean up bucket keys for frontend
        final_trend_data = [{"name": item["name"], "subjects": item["subjects"]} for item in trend_data]

        # 6. Site Status Distribution
        site_status_map = {
            'SELECTED': '已选中',
            'INITIATED': '已启动',
            'ACTIVE': '活跃',
            'CLOSED': '已关闭',
            'TERMINATED': '已终止',
        }
        site_status_distribution = (
            Site.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        
        site_chart_data = [
            {"name": site_status_map.get(item['status'], item['status']), "value": item['count']} 
            for item in site_status_distribution
        ]

        # 7. AE Severity Distribution
        ae_severity_map = {
            'MILD': '轻度',
            'MODERATE': '中度',
            'SEVERE': '重度',
        }
        ae_severity_qs = (
            AdverseEvent.objects.values('severity')
            .annotate(count=Count('id'))
            .order_by('severity')
        )
        ae_severity_data = [
            {"name": ae_severity_map.get(item['severity'], item['severity']), "value": item['count']}
            for item in ae_severity_qs
        ]

        # 8. Query Status Distribution
        query_status_map = {
            'OPEN': '打开',
            'ANSWERED': '已回复',
            'CLOSED': '已关闭',
            'CANCELLED': '已取消',
        }
        query_status_qs = (
            Query.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        query_status_data = [
            {"name": query_status_map.get(item['status'], item['status']), "value": item['count']}
            for item in query_status_qs
        ]

        # 9. Visit Status Distribution
        visit_status_map = {
            'PLANNED': '计划中',
            'COMPLETED': '已完成',
            'MISSED': '失访',
        }
        visit_status_qs = (
            Visit.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        visit_status_data = [
            {"name": visit_status_map.get(item['status'], item['status']), "value": item['count']}
            for item in visit_status_qs
        ]

        # 10. Protocol Deviation Status Distribution
        deviation_status_map = {
            'OPEN': '打开',
            'RESOLVED': '已解决',
            'CAPA_REQUIRED': '需CAPA',
        }
        deviation_status_qs = (
            ProtocolDeviation.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        deviation_status_data = [
            {"name": deviation_status_map.get(item['status'], item['status']), "value": item['count']}
            for item in deviation_status_qs
        ]

        # 11. Monitoring Visit Status Distribution
        monitoring_status_map = {
            'PLANNED': '计划中',
            'SCHEDULED': '已排程',
            'COMPLETED': '已完成',
            'REPORT_DRAFT': '报告草稿',
            'REPORT_FINAL': '报告终稿',
            'CANCELED': '已取消',
        }
        monitoring_status_qs = (
            MonitoringVisit.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        monitoring_status_data = [
            {"name": monitoring_status_map.get(item['status'], item['status']), "value": item['count']}
            for item in monitoring_status_qs
        ]

        data = {
            "trials": {
                "total": total_trials,
                "active": active_trials,
            },
            "subjects": {
                "total": total_subjects,
                "active": active_subjects,
                "enrolled": enrolled_subjects,
            },
            "safety": {
                "pending_saes": pending_saes,
            },
            "sites": {
                "total": total_sites,
                "active": active_sites,
            },
            "charts": {
                "recruitment_trend": final_trend_data,
                "site_distribution": site_chart_data,
                "ae_severity": ae_severity_data,
                "query_status": query_status_data,
                "visit_status": visit_status_data,
                "deviation_status": deviation_status_data,
                "monitoring_status": monitoring_status_data,
            }
        }
        
        return Response(data)
