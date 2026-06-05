from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PM', 'Project Manager'),
        ('CRA', 'Clinical Research Associate'),
        ('DM', 'Data Manager'),
        ('STAT', 'Statistician'),
        ('PV', 'Pharmacovigilance'),
        ('QA', 'Quality Assurance'),
        ('INV', 'Investigator'),
        ('IRB', 'IRB Member'),
        ('ADMIN', 'System Administrator'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CRA')
    organization = models.CharField(max_length=255, blank=True, null=True, help_text="Hospital or CRO name")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False, help_text="Verified by admin")
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
