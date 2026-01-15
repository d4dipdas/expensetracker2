from django import forms
from .models import Income, Expense, Budget, Category, Source
from django.db import models

class DateInput(forms.DateInput):
    input_type = 'date'

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['source', 'amount', 'date', 'description']
        widgets = {
            'date': DateInput(),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'date', 'description']
        widgets = {
            'date': DateInput(),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ExpenseForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(models.Q(user=user) | models.Q(user__isnull=True))

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BudgetForm, self).__init__(*args, **kwargs)
        self.fields['category'].required = False
        if user:
            self.fields['category'].queryset = Category.objects.filter(models.Q(user=user) | models.Q(user__isnull=True))

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ['name']
