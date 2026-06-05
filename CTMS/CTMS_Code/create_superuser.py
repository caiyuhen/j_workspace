import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctms_backend.settings')
django.setup()

from users.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='ADMIN')
    print("Superuser created.")
else:
    print("Superuser already exists.")
