
import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_tracker.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from finance.models import Category, Budget, Expense
from django.core import mail
from datetime import date

def verify_alert():
    print("--- Starting Verification Script ---")
    
    # 1. Setup User and Data
    username = 'verify_user'
    password = 'verify_password'
    email = 'verify@example.com'
    
    user, created = User.objects.get_or_create(username=username, email=email)
    if created:
        user.set_password(password)
        user.save()
        print(f"Created user: {username}")
    else:
        print(f"Using existing user: {username}")
        
    category, _ = Category.objects.get_or_create(name='VerifyCategory', user=user)
    print(f"Category: {category.name}")
    
    # 2. Login
    client = Client()
    login_success = client.login(username=username, password=password)
    print(f"Login success: {login_success}")
    
    # 3. Set Budget (e.g., 500)
    # BudgetForm fields: amount, category, start_date, end_date
    print("Setting Budget to 500...")
    client.post('/set-budget/', {
        'amount': 500,
        'category': category.id,
        'start_date': '2026-01-01',
        'end_date': '2026-01-31'
    })
    
    # Verify Budget Created
    budget = Budget.objects.filter(user=user, category=category).first()
    print(f"Budget created: {budget.amount if budget else 'None'}")

    # 4. Add Expense to Exceed Budget (e.g., 600)
    # ExpenseForm fields: amount, category, date, description
    print("Adding Expense of 600 (should trigger alert)...")
    
    # We need to capture emails. 
    # Since the server settings use 'console', we can't easily capture it here 
    # unless we override the setting *before* the view processes it.
    # However, 'django.test.Client' runs in the same process, so overriding settings here works!
    
    from django.test.utils import override_settings
    
    with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
        response = client.post('/add-expense/', {
            'amount': 600,
            'category': category.id,
            'date': '2026-01-05',
            'description': 'Over budget expense'
        })
        
        # 5. Verify Email
        print(f"Response status: {response.status_code}")
        print(f"Emails sent: {len(mail.outbox)}")
        
        if len(mail.outbox) > 0:
            email = mail.outbox[0]
            print(f"Email Subject: {email.subject}")
            print(f"Email Body Snippet: {email.body[:50]}...")
            print("SUCCESS: Email alert verified!")
        else:
            print("FAILURE: No email sent.")
            # Debug: check expense created
            exp = Expense.objects.filter(user=user, amount=600).first()
            print(f"Expense created: {exp}")

if __name__ == '__main__':
    verify_alert()
