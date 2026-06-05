import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from trials.models import Trial, Site, InvestigationalProduct
from subjects.models import Subject, Visit, Specimen
from documents.models import Document
from monitoring.models import MonitoringVisit, ProtocolDeviation, Query
from safety.models import AdverseEvent

class Command(BaseCommand):
    help = 'Populates the database with demo data for testing purposes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting demo data population...')

        # 1. Create Users
        users = self.create_users()
        
        # 2. Create Trials
        trials = self.create_trials(users['pm'])
        
        # 3. Create Sites
        sites = self.create_sites(trials, users['inv'], users['cra'])
        
        # 4. Create Subjects
        subjects = self.create_subjects(sites)
        
        # 5. Create Visits
        visits = self.create_visits(subjects, users['cra'])
        
        # 6. Create Drugs & Specimens
        self.create_drugs_specimens(trials, subjects)
        
        # 7. Create Documents
        self.create_documents(trials, sites, users['cra'])
        
        # 8. Create Monitoring Data
        self.create_monitoring(sites, users['cra'], visits)
        
        # 9. Create Safety Data
        self.create_safety(subjects, users['inv'])

        # 10. Simulate Updates for Audit Trail
        self.simulate_updates(subjects, trials, users['pm'])

        self.stdout.write(self.style.SUCCESS('Successfully populated demo data!'))

    def create_users(self):
        self.stdout.write('Creating users...')
        roles = {
            'pm': ('Project Manager', 'PM'),
            'cra': ('Clinical Research Associate', 'CRA'),
            'dm': ('Data Manager', 'DM'),
            'stat': ('Statistician', 'STAT'),
            'pv': ('Pharmacovigilance', 'PV'),
            'qa': ('Quality Assurance', 'QA'),
            'inv': ('Investigator', 'INV'),
            'irb': ('IRB Member', 'IRB'),
            'admin': ('System Administrator', 'ADMIN'),
        }
        
        created_users = {}
        for role_key, (_, role_code) in roles.items():
            username = f"{role_key}_user"
            email = f"{role_key}@example.com"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'role': role_code,
                    'is_active': True,
                    'is_staff': role_code == 'ADMIN',
                    'is_superuser': role_code == 'ADMIN',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username}')
            created_users[role_key] = user
            
        return created_users

    def create_trials(self, pm_user):
        self.stdout.write('Creating trials...')
        trials_data = [
            {
                'protocol_number': 'CTMS-2026-001',
                'title': 'Phase III Oncology Study (Lung Cancer)',
                'phase': 'III',
                'sponsor': 'BioPharma Inc.',
                'status': 'ACTIVE',
                'description': 'A randomized, double-blind, placebo-controlled study.',
                'irb_approval_number': 'IRB-2026-001'
            },
            {
                'protocol_number': 'CTMS-2026-002',
                'title': 'Phase I Bioequivalence Study (Generic Drug X)',
                'phase': 'I',
                'sponsor': 'GenericCorp Ltd.',
                'status': 'DRAFT',
                'description': 'Open-label, randomized, two-period crossover study.',
                'irb_approval_number': 'IRB-2026-002'
            }
        ]
        
        created_trials = []
        for data in trials_data:
            trial, created = Trial.objects.get_or_create(
                protocol_number=data['protocol_number'],
                defaults={
                    **data,
                    'project_manager': pm_user,
                    'start_date': timezone.now().date(),
                    'end_date': timezone.now().date() + timedelta(days=365),
                    'irb_approval_date': timezone.now().date() - timedelta(days=30),
                    'db_lock_date': None,
                    'archive_date': None
                }
            )
            if created:
                self.stdout.write(f'Created trial: {trial.protocol_number}')
            created_trials.append(trial)
            
        return created_trials

    def create_sites(self, trials, inv_user, cra_user):
        self.stdout.write('Creating sites...')
        sites = []
        site_data = [
            {'number': '001', 'name': 'General Hospital', 'city': 'New York'},
            {'number': '002', 'name': 'University Medical Center', 'city': 'Boston'},
            {'number': '003', 'name': 'Community Clinic', 'city': 'Chicago'},
        ]
        
        for trial in trials:
            for data in site_data:
                site, created = Site.objects.get_or_create(
                    trial=trial,
                    site_number=data['number'],
                    defaults={
                        'name': data['name'],
                        'principal_investigator': inv_user,
                        'assigned_cra': cra_user,
                        'status': 'ACTIVE' if trial.status == 'ACTIVE' else 'SELECTED',
                        'address': f"123 Medical Way, {data['city']}"
                    }
                )
                if created:
                    self.stdout.write(f'Created site: {site}')
                sites.append(site)
        return sites

    def create_subjects(self, sites):
        self.stdout.write('Creating subjects...')
        subjects = []
        statuses = ['SCREENING', 'ENROLLED', 'ACTIVE', 'COMPLETED', 'SCREEN_FAIL']
        
        for site in sites:
            if site.status != 'ACTIVE':
                continue
                
            for i in range(1, 6):  # 5 subjects per active site
                sub_num = f"{site.site_number}-{i:03d}"
                status = random.choice(statuses)
                
                subject, created = Subject.objects.get_or_create(
                    site=site,
                    subject_number=sub_num,
                    defaults={
                        'subject_initials': f"S{i}T",
                        'status': status,
                        'informed_consent_date': timezone.now().date() - timedelta(days=random.randint(10, 100)),
                        'enrollment_date': timezone.now().date() - timedelta(days=random.randint(1, 50)) if status in ['ENROLLED', 'ACTIVE', 'COMPLETED'] else None
                    }
                )
                if created:
                    self.stdout.write(f'Created subject: {subject}')
                subjects.append(subject)
        return subjects

    def create_visits(self, subjects, monitor):
        self.stdout.write('Creating visits...')
        visit_names = ['Screening', 'Baseline', 'Week 4', 'Week 8', 'Week 12', 'EOT']
        created_visits = []
        
        for subject in subjects:
            for idx, name in enumerate(visit_names):
                status = 'PLANNED'
                visit_date = None
                
                if subject.status == 'SCREEN_FAIL' and idx > 0:
                    break
                
                is_monitored = False
                monitored_by = None
                monitored_at = None
                visit_data = {}

                if subject.status in ['ACTIVE', 'COMPLETED', 'ENROLLED']:
                    if idx <= 2: # Simulate some completed visits
                        status = 'COMPLETED'
                        visit_date = subject.informed_consent_date + timedelta(days=idx*28)
                        
                        # Add realistic data
                        visit_data = {
                            'weight': random.randint(50, 90),
                            'height': random.randint(150, 190),
                            'systolic_bp': random.randint(110, 140),
                            'diastolic_bp': random.randint(70, 90),
                            'temperature': round(random.uniform(36.0, 37.5), 1),
                            'notes': 'Normal findings.'
                        }

                        is_monitored = random.choice([True, False])
                        if is_monitored:
                            monitored_by = monitor
                            monitored_at = timezone.now()
                
                visit, created = Visit.objects.get_or_create(
                    subject=subject,
                    visit_name=name,
                    defaults={
                        'order': idx + 1,
                        'status': status,
                        'visit_date': visit_date,
                        'target_date': subject.informed_consent_date + timedelta(days=idx*28),
                        'data_status': 'VERIFIED' if is_monitored else ('COMPLETE' if status == 'COMPLETED' else 'EMPTY'),
                        'is_monitored': is_monitored,
                        'monitored_by': monitored_by,
                        'monitored_at': monitored_at,
                        'data': visit_data
                    }
                )
                
                # Update existing visits if they lack data
                if not created and status == 'COMPLETED' and not visit.data:
                    visit.data = visit_data
                    visit.data_status = 'VERIFIED' if is_monitored else 'COMPLETE'
                    visit.is_monitored = is_monitored
                    visit.monitored_by = monitored_by
                    visit.monitored_at = monitored_at
                    visit.visit_date = visit_date
                    visit.save()

                created_visits.append(visit)
        return created_visits

    def create_documents(self, trials, sites, uploader):
        self.stdout.write('Creating documents...')
        # Trial level docs
        for trial in trials:
            Document.objects.get_or_create(
                title=f"Protocol {trial.protocol_number} v1.0",
                category='PROTOCOL',
                defaults={
                    'trial': trial,
                    'version': '1.0',
                    'uploaded_by': uploader,
                    'description': 'Initial protocol version'
                }
            )
        
        # Site level docs
        for site in sites:
            Document.objects.get_or_create(
                title=f"CV - PI {site.name}",
                category='OTHER',
                defaults={
                    'site': site,
                    'uploaded_by': uploader,
                    'description': 'Curriculum Vitae of Principal Investigator'
                }
            )

    def create_drugs_specimens(self, trials, subjects):
        self.stdout.write('Creating drugs and specimens...')
        for trial in trials:
            InvestigationalProduct.objects.get_or_create(
                trial=trial,
                name=f"Study Drug {trial.protocol_number}",
                defaults={
                    'product_type': 'DRUG',
                    'batch_number': f"LOT-{random.randint(1000, 9999)}",
                    'expiry_date': timezone.now().date() + timedelta(days=500),
                    'quantity': 1000,
                    'description': 'Main investigational product for the study.'
                }
            )
        
        for subject in subjects:
            if subject.status in ['ACTIVE', 'COMPLETED', 'ENROLLED']:
                # Create Blood Specimen
                Specimen.objects.get_or_create(
                    specimen_id=f"SPEC-{subject.subject_number}-BLD",
                    defaults={
                        'subject': subject,
                        'specimen_type': 'BLOOD',
                        'collection_date': timezone.now() - timedelta(days=random.randint(1, 30)),
                        'storage_location': f"FREEZER-{random.randint(1, 10)}",
                        'status': 'COLLECTED'
                    }
                )
                
                # Create Urine Specimen
                Specimen.objects.get_or_create(
                    specimen_id=f"SPEC-{subject.subject_number}-URN",
                    defaults={
                        'subject': subject,
                        'specimen_type': 'URINE',
                        'collection_date': timezone.now() - timedelta(days=random.randint(1, 30)),
                        'storage_location': f"FRIDGE-{random.randint(1, 5)}",
                        'status': 'COLLECTED'
                    }
                )

    def create_monitoring(self, sites, monitor, visits):
        self.stdout.write('Creating monitoring data...')
        for site in sites:
            # Monitoring Visit - SIV
            MonitoringVisit.objects.get_or_create(
                site=site,
                visit_type='SIV',
                defaults={
                    'monitor': monitor,
                    'status': 'COMPLETED',
                    'planned_date': timezone.now().date() - timedelta(days=60),
                    'actual_date': timezone.now().date() - timedelta(days=60),
                    'report_content': 'Site initiated successfully. Staff trained.'
                }
            )
            
            # Monitoring Visit - RMV (Regular Monitoring Visit)
            MonitoringVisit.objects.get_or_create(
                site=site,
                visit_type='RMV',
                defaults={
                    'monitor': monitor,
                    'status': 'PLANNED',
                    'planned_date': timezone.now().date() + timedelta(days=30),
                    'report_content': ''
                }
            )
            
            # Protocol Deviation
            if random.choice([True, False]):
                if not ProtocolDeviation.objects.filter(
                    trial=site.trial,
                    site=site,
                    description='Missed reporting window for SAE'
                ).exists():
                    ProtocolDeviation.objects.create(
                        trial=site.trial,
                        site=site,
                        description='Missed reporting window for SAE',
                        date_occurred=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                        date_identified=timezone.now().date(),
                        severity='MAJOR',
                        status='OPEN',
                        reported_by=monitor
                    )

        # Create Queries for completed visits
        for visit in visits:
            if visit.status == 'COMPLETED' and random.random() < 0.4:
                if not Query.objects.filter(visit=visit, query_text__startswith="Please clarify").exists():
                    status = random.choice(['OPEN', 'ANSWERED', 'CLOSED', 'CANCELLED'])
                    answer = 'Value confirmed as correct.' if status in ['ANSWERED', 'CLOSED'] else ''
                    
                    Query.objects.create(
                        visit=visit,
                        query_text=f"Please clarify the value for field 'weight' in visit {visit.visit_name}",
                        raised_by=monitor,
                        status=status,
                        answer_text=answer,
                        answered_by=monitor if status != 'OPEN' else None
                    )

    def create_safety(self, subjects, reporter):
        self.stdout.write('Creating safety data...')
        for subject in subjects:
            if random.random() < 0.3: # 30% chance of AE
                if not AdverseEvent.objects.filter(subject=subject, event_term__startswith='Adverse Event').exists():
                    severity = random.choice(['MILD', 'MODERATE', 'SEVERE'])
                    AdverseEvent.objects.create(
                        subject=subject,
                        event_term=f'Adverse Event - {random.choice(["Headache", "Nausea", "Dizziness", "Fatigue"])}',
                        onset_date=timezone.now().date() - timedelta(days=random.randint(1, 10)),
                        severity=severity,
                        is_serious='NO',
                        relationship=random.choice(['NOT_RELATED', 'POSSIBLY', 'PROBABLY']),
                        outcome='RECOVERED',
                        reporter=reporter
                    )
            
            if random.random() < 0.1: # 10% chance of SAE
                if not AdverseEvent.objects.filter(subject=subject, event_term='Severe Allergic Reaction').exists():
                    AdverseEvent.objects.create(
                        subject=subject,
                        event_term='Severe Allergic Reaction',
                        onset_date=timezone.now().date() - timedelta(days=random.randint(1, 20)),
                        severity='SEVERE',
                        is_serious='YES',
                        relationship='PROBABLY',
                        outcome='RECOVERING',
                        reporter=reporter,
                        is_susar=True,
                        reported_to_pv_at=timezone.now()
                    )

    def simulate_updates(self, subjects, trials, editor):
        self.stdout.write('Simulating updates for audit trail...')
        
        # Update some subjects
        for subject in subjects:
            if random.random() < 0.2: # 20% chance
                old_status = subject.status
                if subject.status == 'SCREENING':
                    subject.status = 'ENROLLED'
                    subject.enrollment_date = timezone.now().date()
                    subject._history_user = editor
                    subject.save() # This triggers audit log
                    self.stdout.write(f"Updated subject {subject.subject_number} status from {old_status} to ENROLLED")

        # Update some trials
        for trial in trials:
            if random.random() < 0.5:
                trial.description += " (Updated description via demo script)"
                trial._history_user = editor
                trial.save()
                self.stdout.write(f"Updated trial {trial.protocol_number} description")

        # Update Monitoring Visits
        mvs = MonitoringVisit.objects.all()
        for mv in mvs:
            if random.random() < 0.3:
                old_status = mv.status
                mv.status = random.choice(['REPORT_DRAFT', 'REPORT_FINAL', 'COMPLETED'])
                mv._history_user = editor
                mv.save()
                self.stdout.write(f"Updated MonitoringVisit {mv.id} status from {old_status} to {mv.status}")

        # Update Protocol Deviations
        pds = ProtocolDeviation.objects.all()
        for pd in pds:
            if random.random() < 0.3:
                old_status = pd.status
                pd.status = 'RESOLVED'
                pd.corrective_action = 'Retraining provided.'
                pd._history_user = editor
                pd.save()
                self.stdout.write(f"Updated ProtocolDeviation {pd.id} status from {old_status} to RESOLVED")
