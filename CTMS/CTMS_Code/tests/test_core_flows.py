import pytest
from users.models import User
from trials.models import Trial, Site
from subjects.models import Subject
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestCTMSFlow:
    def setup_method(self):
        self.client = APIClient()
        # Create Users
        self.pm = User.objects.create_user(username='pm1', password='password', role='PM')
        self.cra = User.objects.create_user(username='cra1', password='password', role='CRA')
        self.inv = User.objects.create_user(username='inv1', password='password', role='INV')
        self.admin = User.objects.create_superuser(username='admin_test', password='password', role='ADMIN')

    def test_trial_creation_by_pm(self):
        self.client.force_authenticate(user=self.pm)
        data = {
            "protocol_number": "CTMS-001",
            "title": "Test Trial Phase I",
            "phase": "I",
            "sponsor": "Pharma Corp",
            "status": "DRAFT"
        }
        response = self.client.post('/api/v1/trials/', data)
        assert response.status_code == 201
        assert Trial.objects.count() == 1
        assert Trial.objects.first().project_manager == self.pm

    def test_site_creation_and_assignment(self):
        trial = Trial.objects.create(protocol_number="CTMS-002", title="Test 2", phase="II", sponsor="Sponsor", project_manager=self.pm)
        
        self.client.force_authenticate(user=self.pm)
        data = {
            "trial": trial.id,
            "site_number": "001",
            "name": "General Hospital",
            "principal_investigator": self.inv.id,
            "assigned_cra": self.cra.id,
            "address": "123 Medical Way"
        }
        response = self.client.post('/api/v1/sites/', data)
        assert response.status_code == 201
        
        site = Site.objects.get(site_number="001")
        assert site.principal_investigator == self.inv
        assert site.assigned_cra == self.cra

    def test_subject_enrollment_by_inv(self):
        trial = Trial.objects.create(protocol_number="CTMS-003", title="Test 3", phase="III", sponsor="Sponsor", project_manager=self.pm)
        site = Site.objects.create(trial=trial, site_number="002", name="Clinic", principal_investigator=self.inv, address="Address")
        
        self.client.force_authenticate(user=self.inv)
        data = {
            "site": site.id,
            "subject_initials": "JD",
            "subject_number": "S-001",
            "informed_consent_date": "2023-01-01",
            "status": "SCREENING"
        }
        response = self.client.post('/api/v1/subjects/', data)
        assert response.status_code == 201
        assert Subject.objects.count() == 1
        
    def test_inv_cannot_add_subject_to_other_site(self):
        other_inv = User.objects.create_user(username='inv2', password='password', role='INV')
        trial = Trial.objects.create(protocol_number="CTMS-004", title="Test 4", phase="III", sponsor="Sponsor", project_manager=self.pm)
        site = Site.objects.create(trial=trial, site_number="003", name="Other Clinic", principal_investigator=other_inv, address="Address")
        
        self.client.force_authenticate(user=self.inv) # Authenticated as inv1, trying to add to inv2's site
        data = {
            "site": site.id,
            "subject_initials": "XX",
            "subject_number": "S-002",
            "informed_consent_date": "2023-01-01",
            "status": "SCREENING"
        }
        response = self.client.post('/api/v1/subjects/', data)
        assert response.status_code == 403 # PermissionDenied

    def test_audit_trail_creation(self):
        self.client.force_authenticate(user=self.pm)
        trial = Trial.objects.create(protocol_number="CTMS-005", title="Audit Test", phase="I", sponsor="Sponsor", project_manager=self.pm)
        
        # Update trial status
        data = {"status": "ACTIVE", "title": "Updated Title"}
        self.client.patch(f'/api/v1/trials/{trial.id}/', data)
        
        # Check history
        assert trial.history.count() > 0
        latest_history = trial.history.first()
        assert latest_history.status == "ACTIVE"
        # Note: history_user is automatically set by middleware in requests, 
        # but in tests we might need to simulate middleware or check logic differently.
        # SimpleHistoryRequestMiddleware captures request.user.
