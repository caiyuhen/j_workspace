from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from users.models import User

class Trial(models.Model):
    PHASE_CHOICES = (
        ('I', 'Phase I'),
        ('II', 'Phase II'),
        ('III', 'Phase III'),
        ('IV', 'Phase IV'),
        ('BE', 'Bioequivalence'),
    )
    
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted to IRB'),
        ('APPROVED', 'IRB Approved'),
        ('ACTIVE', 'Active (Enrolling)'),
        ('LOCKED', 'Database Locked'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
    )

    protocol_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES)
    sponsor = models.CharField(max_length=255)
    project_manager = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role': 'PM'}, related_name='managed_trials')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    irb_approval_date = models.DateField(null=True, blank=True)
    irb_approval_number = models.CharField(max_length=100, blank=True)
    db_lock_date = models.DateField(null=True, blank=True)
    archive_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.protocol_number} - {self.title}"

class Site(models.Model):
    STATUS_CHOICES = (
        ('SELECTED', 'Selected'),
        ('INITIATED', 'Initiated'),
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('TERMINATED', 'Terminated'),
    )
    
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='sites')
    site_number = models.CharField(max_length=20)
    name = models.CharField(max_length=255, help_text="Hospital Name")
    principal_investigator = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role': 'INV'}, related_name='pi_sites')
    assigned_cra = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'CRA'}, related_name='monitored_sites')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SELECTED')
    address = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ('trial', 'site_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.site_number} - {self.name}"

class InvestigationalProduct(models.Model):
    PRODUCT_TYPES = (
        ('DRUG', 'Drug'),
        ('DEVICE', 'Device'),
        ('BIOLOGIC', 'Biologic'),
        ('SUPPLY', 'Supply'),
    )
    
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='DRUG')
    batch_number = models.CharField(max_length=50)
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name} ({self.batch_number})"
