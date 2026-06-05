from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from trials.models import Trial, Site, InvestigationalProduct
from subjects.models import Subject, Visit, Specimen
from safety.models import AdverseEvent
from monitoring.models import Query, MonitoringVisit, ProtocolDeviation
from django.utils import timezone
import datetime

User = get_user_model()

class ValidationOQTests(APITestCase):
    def setUp(self):
        # Create Users
        self.pm = User.objects.create_user(username='pm_user', password='password123', role='PM')
        self.cra = User.objects.create_user(username='cra_user', password='password123', role='CRA')
        self.inv = User.objects.create_user(username='inv_user', password='password123', role='INV')
        self.admin = User.objects.create_superuser(username='admin_user', password='password123', role='ADMIN')

        # Setup basic data
        self.trial = Trial.objects.create(
            protocol_number="OQ-TRIAL-001",
            title="Validation Trial",
            phase="II",
            sponsor="Validation Pharma",
            status="DRAFT",
            project_manager=self.pm
        )
        self.site = Site.objects.create(
            trial=self.trial,
            site_number="101",
            name="Validation Site",
            principal_investigator=self.inv,
            assigned_cra=self.cra,
            address="123 Valid St"
        )
        self.subject = Subject.objects.create(
            site=self.site,
            subject_number="S-101",
            subject_initials="VT",
            informed_consent_date=timezone.now().date(),
            status="SCREENING"
        )
        self.visit = Visit.objects.create(
            subject=self.subject,
            visit_name="Baseline",
            order=1,
            target_date=timezone.now().date()
        )

    # OQ-01: 认证 - 使用有效凭据登录
    def test_oq_01_login_valid_credentials(self):
        url = '/api/v1/token/'
        data = {'username': 'pm_user', 'password': 'password123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    # OQ-02: 认证 - 使用无效凭据登录
    def test_oq_02_login_invalid_credentials(self):
        url = '/api/v1/token/'
        data = {'username': 'pm_user', 'password': 'wrongpassword'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # OQ-03: RBAC - CRA 尝试删除试验
    def test_oq_03_cra_delete_trial_forbidden(self):
        self.client.force_authenticate(user=self.cra)
        url = f'/api/v1/trials/{self.trial.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Trial.objects.filter(id=self.trial.id).exists())

    # OQ-07: 安全性 - 报告者提交 SAE
    def test_oq_07_report_sae(self):
        self.client.force_authenticate(user=self.inv) # Assuming INV reports SAE
        url = '/api/v1/adverse-events/'
        data = {
            'subject': self.subject.id,
            'event_term': 'Severe Headache',
            'onset_date': timezone.now().isoformat(),
            'severity': 'SEVERE',
            'is_serious': 'YES', # SAE
            'relationship': 'POSSIBLY',
            'outcome': 'UNKNOWN'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AdverseEvent.objects.filter(event_term='Severe Headache', is_serious='YES').exists())

    # OQ-09: SDV - CRA 标记访视为已核查
    def test_oq_09_cra_verify_visit(self):
        self.client.force_authenticate(user=self.cra)
        # Assuming there's an action or patch to verify
        url = f'/api/v1/visits/{self.visit.id}/'
        data = {'is_monitored': True, 'data_status': 'VERIFIED'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.visit.refresh_from_db()
        self.assertTrue(self.visit.is_monitored)
        self.assertEqual(self.visit.data_status, 'VERIFIED')

    # OQ-11: IRB - 未经 IRB 批准试验状态不能为进行中
    # This might require custom validation logic in serializer/model. 
    # Let's assume the requirement is that we can't set status to ACTIVE without irb_approval_date
    def test_oq_11_trial_status_active_requires_irb(self):
        self.client.force_authenticate(user=self.pm)
        url = f'/api/v1/trials/{self.trial.id}/'
        # Try to set ACTIVE without IRB date
        data = {'status': 'ACTIVE'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data_valid = {
            'status': 'ACTIVE',
            'irb_approval_date': timezone.now().date(),
            'irb_approval_number': 'IRB-123'
        }
        response = self.client.patch(url, data_valid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trial.refresh_from_db()
        self.assertEqual(self.trial.status, 'ACTIVE')

    # OQ-12: 药物 - 向试验添加新研究药物
    def test_oq_12_add_investigational_product(self):
        self.client.force_authenticate(user=self.pm)
        url = '/api/v1/products/'
        data = {
            'trial': self.trial.id,
            'name': 'Test Drug A',
            'product_type': 'DRUG',
            'batch_number': 'BATCH-001',
            'expiry_date': (timezone.now() + datetime.timedelta(days=365)).date(),
            'quantity': 1000
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(InvestigationalProduct.objects.filter(batch_number='BATCH-001').exists())

    # OQ-13: 样本 - 为入组受试者添加样本
    def test_oq_13_add_specimen(self):
        self.client.force_authenticate(user=self.inv)
        url = '/api/v1/specimens/'
        data = {
            'subject': self.subject.id,
            'specimen_id': 'SPEC-001', # Correct field name
            'specimen_type': 'BLOOD',
            'collection_date': timezone.now().isoformat(),
            'storage_location': 'Freezer 1', # Correct field name
            'status': 'COLLECTED'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Specimen.objects.filter(specimen_id='SPEC-001').exists())

    # OQ-14: 导出 - PM 导出试验列表为 CSV
    # Export is implemented on client-side. Backend provides list API.
    def test_oq_14_export_trials_api_availability(self):
        self.client.force_authenticate(user=self.pm)
        url = '/api/v1/trials/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Frontend uses this data to generate CSV

    # OQ-15: 质疑 - CRA 对访视提出质疑
    def test_oq_15_raise_query(self):
        self.client.force_authenticate(user=self.cra)
        url = '/api/v1/queries/'
        data = {
            'visit': self.visit.id,
            'query_text': 'Missing lab report?',
            'status': 'OPEN'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Query.objects.filter(query_text='Missing lab report?').exists())

    # OQ-17: 审计 - 创建监查访视
    def test_oq_17_create_monitoring_visit(self):
        self.client.force_authenticate(user=self.cra)
        url = '/api/v1/monitoring-visits/'
        data = {
            'site': self.site.id,
            'monitor': self.cra.id,
            'visit_type': 'RMV',
            'status': 'PLANNED',
            'planned_date': (timezone.now() + datetime.timedelta(days=7)).date()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MonitoringVisit.objects.filter(visit_type='RMV').exists())

    # OQ-18: 审计 - 记录方案违背
    def test_oq_18_record_protocol_deviation(self):
        self.client.force_authenticate(user=self.cra)
        url = '/api/v1/protocol-deviations/'
        data = {
            'trial': self.trial.id,
            'site': self.site.id,
            'subject': self.subject.id,
            'description': 'Missed window',
            'date_occurred': timezone.now().date(),
            'date_identified': timezone.now().date(),
            'severity': 'MINOR',
            'status': 'OPEN'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProtocolDeviation.objects.filter(description='Missed window').exists())

    # OQ-19: 审计 - 导出审计追踪为 CSV
    def test_oq_19_export_audit_trail_api_availability(self):
        self.client.force_authenticate(user=self.pm)
        # Ensure some history exists for MonitoringVisit
        mv = MonitoringVisit.objects.create(
            site=self.site,
            monitor=self.cra,
            visit_type='SIV',
            planned_date=timezone.now().date()
        )
        
        url = '/api/v1/audit-logs/?model=MonitoringVisit'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)
