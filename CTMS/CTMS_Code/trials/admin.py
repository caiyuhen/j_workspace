from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Trial, Site

class SiteInline(admin.TabularInline):
    model = Site
    extra = 1

@admin.register(Trial)
class TrialAdmin(SimpleHistoryAdmin):
    list_display = ('protocol_number', 'title', 'phase', 'status', 'project_manager')
    list_filter = ('phase', 'status')
    search_fields = ('protocol_number', 'title')
    inlines = [SiteInline]

@admin.register(Site)
class SiteAdmin(SimpleHistoryAdmin):
    list_display = ('site_number', 'name', 'trial', 'status', 'principal_investigator', 'assigned_cra')
    list_filter = ('status', 'trial')
    search_fields = ('site_number', 'name', 'trial__protocol_number')
