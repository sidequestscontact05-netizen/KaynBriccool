import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='sidequests.contact05@gmail.com').exists():
    User.objects.create_superuser(email='sidequests.contact05@gmail.com', password='admin123', full_name='Admin KaynBricool')
    print('Admin created successfully')
else:
    u = User.objects.get(email='sidequests.contact05@gmail.com')
    u.set_password('admin123')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print('Admin password updated')
