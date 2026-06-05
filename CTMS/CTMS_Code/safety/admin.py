from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import AdverseEvent

@admin.register(AdverseEvent)
class AdverseEventAdmin(SimpleHistoryAdmin):
    list_display = ('subject', 'event_term', 'onset_date', 'severity', 'is_serious', 'is_susar', 'reporter')
    list_filter = ('is_serious', 'is_susar', 'severity', 'relationship', 'outcome')
    search_fields = ('event_term', 'subject__subject_number')
