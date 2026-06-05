from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Subject, Visit

class VisitInline(admin.TabularInline):
    model = Visit
    extra = 0

@admin.register(Subject)
class SubjectAdmin(SimpleHistoryAdmin):
    list_display = ('subject_number', 'site', 'status', 'enrollment_date', 'informed_consent_date')
    list_filter = ('status', 'site__trial', 'site')
    search_fields = ('subject_number',)
    inlines = [VisitInline]

@admin.register(Visit)
class VisitAdmin(SimpleHistoryAdmin):
    list_display = ('subject', 'visit_name', 'target_date', 'visit_date', 'status', 'data_status')
    list_filter = ('status', 'data_status', 'subject__site__trial')
