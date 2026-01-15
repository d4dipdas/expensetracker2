import os
import django
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_tracker.settings')
django.setup()

# Try import
try:
    import reports.urls
    print("Successfully imported reports.urls")
except ImportError as e:
    print(f"Error importing reports.urls: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Other error: {e}")
    sys.exit(1)
