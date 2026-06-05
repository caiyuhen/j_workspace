from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from subjects.models import Subject, Visit, SignatureLog
from trials.models import Trial, Site
from django.utils import timezone

User = get_user_model()

from django.urls import reverse

class SignatureTests(TestCase):
    def setUp(self):
        # ... existing setup ...
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password123', role='CRA')
        self.client.force_authenticate(user=self.user)
        
        self.trial = Trial.objects.create(
            protocol_number='T001',
            title='Test Trial',
            phase='Phase I',
            status='ACTIVE',
            start_date=timezone.now().date(),
            project_manager=self.user
        )
        
        self.site = Site.objects.create(
            site_number='S001',
            name='Test Site',
            trial=self.trial,
            principal_investigator=self.user,
            assigned_cra=self.user
        )
        
        self.subject = Subject.objects.create(
            subject_number='SUB-001',
            site=self.site,
            informed_consent_date=timezone.now().date()
        )
        
        self.visit = Visit.objects.create(
            subject=self.subject,
            visit_name='Visit 1',
            order=1,
            target_date=timezone.now().date()
        )

    def test_sign_visit_success(self):
        url = reverse('visit-sign-visit', kwargs={'pk': self.visit.id})
        data = {
            'password': 'password123',
            'reason': 'Verified by CRA'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.data_status, 'SIGNED')
        
        # Verify SignatureLog
        log = SignatureLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.visit, self.visit)
        self.assertEqual(log.signer, self.user)
        self.assertEqual(log.reason, 'Verified by CRA')
        
    def test_sign_visit_invalid_password(self):
        url = reverse('visit-sign-visit', kwargs={'pk': self.visit.id})
        data = {
            'password': 'wrongpassword',
            'reason': 'Should fail'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.visit.refresh_from_db()
        self.assertNotEqual(self.visit.data_status, 'SIGNED')
        
        self.assertEqual(SignatureLog.objects.count(), 0)

    def test_sign_visit_missing_password(self):
        url = reverse('visit-sign-visit', kwargs={'pk': self.visit.id})
        data = {
            'reason': 'Missing password'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
