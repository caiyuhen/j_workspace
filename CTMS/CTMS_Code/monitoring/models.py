from django.db import models
from users.models import User
from trials.models import Trial, Site
from subjects.models import Subject, Visit
from simple_history.models import HistoricalRecords

class MonitoringVisit(models.Model):
    VISIT_TYPE_CHOICES = (
        ('SSV', 'Site Selection Visit'),
        ('SIV', 'Site Initiation Visit'),
        ('RMV', 'Routine Monitoring Visit'),
        ('COV', 'Close-out Visit'),
    )
    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('REPORT_DRAFT', 'Report Draft'),
        ('REPORT_FINAL', 'Report Finalized'),
        ('CANCELED', 'Canceled'),
    )

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='monitoring_visits')
    monitor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='monitoring_visits')
    visit_type = models.CharField(max_length=10, choices=VISIT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    
    report_content = models.TextField(blank=True, help_text="Detailed visit report")
    follow_up_items = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.get_visit_type_display()} - {self.site.name} ({self.planned_date})"

class ProtocolDeviation(models.Model):
    SEVERITY_CHOICES = (
        ('MINOR', 'Minor'),
        ('MAJOR', 'Major'),
        ('CRITICAL', 'Critical'),
    )
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('RESOLVED', 'Resolved'),
        ('CAPA_REQUIRED', 'CAPA Required'),
    )

    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='deviations')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='deviations')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='deviations')
    
    description = models.TextField()
    date_occurred = models.DateField()
    date_identified = models.DateField()
    
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MINOR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    
    reported_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_deviations')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"Deviation: {self.description[:50]} ({self.severity})"

class Query(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('ANSWERED', 'Answered'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='queries')
    query_text = models.TextField()
    raised_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='raised_queries')
    
    answer_text = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='answered_queries', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"Query: {self.query_text[:50]} ({self.status})"
