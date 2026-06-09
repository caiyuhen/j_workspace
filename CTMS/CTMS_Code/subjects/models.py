<<<<<<< HEAD
<<<<<<< HEAD
from django.db import models
from trials.models import Site
from simple_history.models import HistoricalRecords

from django.conf import settings

class Subject(models.Model):
    STATUS_CHOICES = (
        ('SCREENING', 'Screening'),
        ('SCREEN_FAIL', 'Screen Failure'),
        ('ENROLLED', 'Enrolled'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn'),
    )

    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='subjects')
    subject_initials = models.CharField(max_length=5)
    subject_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCREENING')
    
    informed_consent_date = models.DateField(help_text="Date ICF signed")
    enrollment_date = models.DateField(null=True, blank=True)
    withdrawal_date = models.DateField(null=True, blank=True)
    withdrawal_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ('site', 'subject_number')

    def __str__(self):
        return f"{self.subject_number} ({self.status})"

class Specimen(models.Model):
    SPECIMEN_TYPES = (
        ('BLOOD', 'Blood'),
        ('URINE', 'Urine'),
        ('TISSUE', 'Tissue'),
        ('SERUM', 'Serum'),
        ('OTHER', 'Other'),
    )
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='specimens')
    specimen_id = models.CharField(max_length=50, unique=True)
    specimen_type = models.CharField(max_length=20, choices=SPECIMEN_TYPES)
    collection_date = models.DateTimeField()
    storage_location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='COLLECTED')
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.specimen_id} ({self.specimen_type})"

class Visit(models.Model):
    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
    )
    DATA_STATUS_CHOICES = (
        ('EMPTY', 'Empty'),
        ('PARTIAL', 'Partial'),
        ('COMPLETE', 'Complete'),
        ('VERIFIED', 'Verified (SDV Done)'),
        ('SIGNED', 'Signed (e-Signature)'),
        ('LOCKED', 'Locked'),
    )

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='visits')
    visit_name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(help_text="Visit sequence order")
    
    target_date = models.DateField(help_text="Projected visit date based on protocol")
    visit_date = models.DateField(null=True, blank=True, help_text="Actual visit date")
    window_days = models.PositiveIntegerField(default=7, help_text="+/- days allowed")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    data_status = models.CharField(max_length=20, choices=DATA_STATUS_CHOICES, default='EMPTY')
    is_monitored = models.BooleanField(default=False, help_text="SDV Completed")
    monitored_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='monitored_visits')
    monitored_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True, help_text="CRF Data")
    
    comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['subject', 'order']
        unique_together = ('subject', 'visit_name')

    def __str__(self):
        return f"{self.visit_name} - {self.subject}"

class SignatureLog(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='signatures')
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-signed_at']

    def __str__(self):
        return f"Signed by {self.signer} on {self.signed_at}"
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
from django.db import models
from trials.models import Site
from simple_history.models import HistoricalRecords

from django.conf import settings

class Subject(models.Model):
    STATUS_CHOICES = (
        ('SCREENING', 'Screening'),
        ('SCREEN_FAIL', 'Screen Failure'),
        ('ENROLLED', 'Enrolled'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn'),
    )

    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='subjects')
    subject_initials = models.CharField(max_length=5)
    subject_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCREENING')
    
    informed_consent_date = models.DateField(help_text="Date ICF signed")
    enrollment_date = models.DateField(null=True, blank=True)
    withdrawal_date = models.DateField(null=True, blank=True)
    withdrawal_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ('site', 'subject_number')

    def __str__(self):
        return f"{self.subject_number} ({self.status})"

class Specimen(models.Model):
    SPECIMEN_TYPES = (
        ('BLOOD', 'Blood'),
        ('URINE', 'Urine'),
        ('TISSUE', 'Tissue'),
        ('SERUM', 'Serum'),
        ('OTHER', 'Other'),
    )
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='specimens')
    specimen_id = models.CharField(max_length=50, unique=True)
    specimen_type = models.CharField(max_length=20, choices=SPECIMEN_TYPES)
    collection_date = models.DateTimeField()
    storage_location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='COLLECTED')
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.specimen_id} ({self.specimen_type})"

class Visit(models.Model):
    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
    )
    DATA_STATUS_CHOICES = (
        ('EMPTY', 'Empty'),
        ('PARTIAL', 'Partial'),
        ('COMPLETE', 'Complete'),
        ('VERIFIED', 'Verified (SDV Done)'),
        ('SIGNED', 'Signed (e-Signature)'),
        ('LOCKED', 'Locked'),
    )

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='visits')
    visit_name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(help_text="Visit sequence order")
    
    target_date = models.DateField(help_text="Projected visit date based on protocol")
    visit_date = models.DateField(null=True, blank=True, help_text="Actual visit date")
    window_days = models.PositiveIntegerField(default=7, help_text="+/- days allowed")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    data_status = models.CharField(max_length=20, choices=DATA_STATUS_CHOICES, default='EMPTY')
    is_monitored = models.BooleanField(default=False, help_text="SDV Completed")
    monitored_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='monitored_visits')
    monitored_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True, help_text="CRF Data")
    
    comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['subject', 'order']
        unique_together = ('subject', 'visit_name')

    def __str__(self):
        return f"{self.visit_name} - {self.subject}"

class SignatureLog(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='signatures')
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-signed_at']

    def __str__(self):
        return f"Signed by {self.signer} on {self.signed_at}"
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
