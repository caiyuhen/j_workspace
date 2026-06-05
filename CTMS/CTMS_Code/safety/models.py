from django.db import models
from subjects.models import Subject
from users.models import User
from simple_history.models import HistoricalRecords

class AdverseEvent(models.Model):
    SEVERITY_CHOICES = (
        ('MILD', 'Mild'),
        ('MODERATE', 'Moderate'),
        ('SEVERE', 'Severe'),
    )
    SERIOUS_CHOICES = (
        ('YES', 'Yes (SAE)'),
        ('NO', 'No (AE)'),
    )
    RELATIONSHIP_CHOICES = (
        ('NOT_RELATED', 'Not Related'),
        ('UNLIKELY', 'Unlikely Related'),
        ('POSSIBLY', 'Possibly Related'),
        ('PROBABLY', 'Probably Related'),
        ('DEFINITELY', 'Definitely Related'),
    )
    OUTCOME_CHOICES = (
        ('RECOVERED', 'Recovered/Resolved'),
        ('RECOVERING', 'Recovering/Resolving'),
        ('NOT_RECOVERED', 'Not Recovered/Not Resolved'),
        ('RECOVERED_WITH_SEQUELAE', 'Recovered/Resolved with Sequelae'),
        ('FATAL', 'Fatal'),
        ('UNKNOWN', 'Unknown'),
    )

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='adverse_events')
    event_term = models.CharField(max_length=255, help_text="AE description")
    onset_date = models.DateTimeField()
    resolution_date = models.DateTimeField(null=True, blank=True)
    
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    is_serious = models.CharField(max_length=5, choices=SERIOUS_CHOICES, default='NO')
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    outcome = models.CharField(max_length=30, choices=OUTCOME_CHOICES)
    
    meddra_code = models.CharField(max_length=100, blank=True, null=True, help_text="System Organ Class / Preferred Term")
    
    # SAE Details (if applicable)
    is_susar = models.BooleanField(default=False, help_text="Suspected Unexpected Serious Adverse Reaction")
    reported_to_pv_at = models.DateTimeField(null=True, blank=True)
    reported_to_regulatory_at = models.DateTimeField(null=True, blank=True)
    
    reporter = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_aes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.subject.subject_number} - {self.event_term} ({self.is_serious})"
