import os
import sys
import django
from pathlib import Path
from django.contrib.auth.models import User

# Get the absolute path to your Django project directory
project_path = Path(__file__).resolve().parent

# Add the project directory to the Python path
sys.path.append(str(project_path))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_finance.settings')
django.setup()



def create_superuser():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser created successfully!")
    else:
        print("Superuser already exists.")

create_superuser()
