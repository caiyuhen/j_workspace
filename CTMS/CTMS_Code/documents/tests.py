from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from documents.models import Document
from trials.models import Trial, Site

User = get_user_model()

class DocumentCreationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123', role='PM')
        self.create_url = reverse('document-list')

    def test_create_online_document_payload(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Online Doc",
            "category": "PROTOCOL",
            "version": "1.0",
            "trial": None,
            "site": None,
            "description": "Description",
            "is_online": True
        }
        response = self.client.post(self.create_url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Document.objects.filter(title="Online Doc").exists())
        doc = Document.objects.get(title="Online Doc")
        self.assertTrue(doc.is_online)
        # Check that file is empty (might be empty string or None depending on storage)
        self.assertFalse(bool(doc.file))

    def test_create_online_document_with_trial(self):
        self.client.force_authenticate(user=self.user)
        # Create a trial first
        trial = Trial.objects.create(
            protocol_number="TRIAL-001",
            title="Test Trial",
            phase="PHASE_1",
            status="PLANNING",
            sponsor="Sponsor X",
            project_manager=self.user
        )
        
        data = {
            "title": "Online Doc with Trial",
            "category": "PROTOCOL",
            "version": "1.0",
            "trial": trial.id,
            "site": None,
            "description": "Description",
            "is_online": True
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc = Document.objects.get(title="Online Doc with Trial")
        self.assertEqual(doc.trial, trial)

    def test_create_online_document_missing_title(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "",
            "category": "PROTOCOL",
            "version": "1.0",
            "trial": None,
            "site": None,
            "description": "Description",
            "is_online": True
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

class DocumentLockingTests(APITestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password123', role='PM')
        self.user2 = User.objects.create_user(username='user2', password='password123', role='PM')
        
        # Create a document
        self.document = Document.objects.create(
            title='Test Document',
            version='1.0',
            content='Initial content',
            is_online=True,
            uploaded_by=self.user1
        )
        
        self.lock_url = reverse('document-lock', kwargs={'pk': self.document.pk})
        self.unlock_url = reverse('document-unlock', kwargs={'pk': self.document.pk})
        self.save_url = reverse('document-save-content', kwargs={'pk': self.document.pk})
        self.detail_url = reverse('document-detail', kwargs={'pk': self.document.pk})

    def test_locking_flow(self):
        # 1. User 1 locks the document
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.lock_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.locked_by, self.user1)
        
        # 2. User 2 tries to lock the document (should fail)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.lock_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        
        # 3. User 2 tries to save content (should fail)
        response = self.client.post(self.save_url, {'content': 'Hacked content'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 4. User 1 saves content (should succeed)
        self.client.force_authenticate(user=self.user1)
        new_content = 'Updated content by user 1'
        response = self.client.post(self.save_url, {'content': new_content})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.content, new_content)
        
        # 5. User 1 unlocks the document
        response = self.client.post(self.unlock_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertIsNone(self.document.locked_by)
        
        # 6. User 2 locks the document (should succeed now)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.lock_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.locked_by, self.user2)
