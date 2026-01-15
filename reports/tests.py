from django.test import TestCase, Client
from django.contrib.auth.models import User
from finance.models import Expense, Category, Income, Source, Budget
from django.urls import reverse
import datetime

class ReportsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        self.category = Category.objects.create(name='Food', user=self.user)
        self.source = Source.objects.create(name='Salary', user=self.user)
        
        # Create Data
        Expense.objects.create(
            user=self.user,
            category=self.category,
            amount=150.00,
            date=datetime.date.today(),
            description='Lunch'
        )
        
        Income.objects.create(
            user=self.user,
            source=self.source,
            amount=1000.00,
            date=datetime.date.today(),
            description='Monthly Salary'
        )
        
        # Create Budget
        today = datetime.date.today()
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=100.00,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=30)
        )

    def test_dashboard_view_context(self):
        response = self.client.get(reverse('reports_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/index.html')
        
        # Check context data
        context = response.context
        self.assertIn('budget_data', context)
        self.assertIn('expense_breakdown', context)
        self.assertIn('income_breakdown', context)
        
        # Verify Budget Analysis
        budget_data = context['budget_data'][0]
        self.assertEqual(budget_data['category'], 'Food')
        self.assertEqual(budget_data['limit'], 100.00)
        self.assertEqual(budget_data['spent'], 150.00)
        self.assertTrue(budget_data['is_exceeded'])
        
        # Verify Breakdown
        expense_breakdown = context['expense_breakdown'][0]
        self.assertEqual(expense_breakdown['category__name'], 'Food')
        self.assertEqual(expense_breakdown['total'], 150.00)

    def test_expense_category_data(self):
        response = self.client.get(reverse('expense_category_data'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('labels', data)
        self.assertEqual(data['labels'][0], 'Food')

    def test_income_expense_data(self):
        response = self.client.get(reverse('income_expense_data'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('income', data)
