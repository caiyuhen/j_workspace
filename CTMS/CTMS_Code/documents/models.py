from django.db import models
from users.models import User
from trials.models import Trial, Site
from simple_history.models import HistoricalRecords

class Document(models.Model):
    CATEGORY_CHOICES = (
        ('PROTOCOL', 'Protocol'),
        ('ICF', 'Informed Consent Form'),
        ('IB', 'Investigator Brochure'),
        ('CRF', 'Case Report Form'),
        ('MVR', 'Monitoring Visit Report'),
        ('ETHICS', 'Ethics Approval'),
        ('OTHER', 'Other'),
    )

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    version = models.CharField(max_length=20, default='1.0')
    file = models.FileField(upload_to='documents/%Y/%m/%d/', blank=True, null=True)
    
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_documents')
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Online Editing Fields
    content = models.TextField(blank=True, null=True, help_text="Content for online documents")
    is_online = models.BooleanField(default=False, help_text="True if document is created/edited online")
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_documents')
    locked_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (v{self.version})"
