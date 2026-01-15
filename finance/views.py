from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from .models import Income, Expense, Budget, Category, Source
from .forms import IncomeForm, ExpenseForm, BudgetForm, CategoryForm, SourceForm
import datetime
import csv
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
import json

def _month_bounds(date_obj):
    start = datetime.date(date_obj.year, date_obj.month, 1)
    if date_obj.month == 12:
        next_month = datetime.date(date_obj.year + 1, 1, 1)
    else:
        next_month = datetime.date(date_obj.year, date_obj.month + 1, 1)
    end = next_month - datetime.timedelta(days=1)
    return start, end

@login_required(login_url='login')
def export_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expense_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Category/Source', 'Amount', 'Description'])

    incomes = Income.objects.filter(user=request.user)
    expenses = Expense.objects.filter(user=request.user)

    transactions = []
    for income in incomes:
        transactions.append({
            'date': income.date,
            'type': 'Income',
            'category': income.source.name if income.source else 'N/A',
            'amount': income.amount,
            'description': income.description
        })
    
    for expense in expenses:
        transactions.append({
            'date': expense.date,
            'type': 'Expense',
            'category': expense.category.name if expense.category else 'N/A',
            'amount': expense.amount,
            'description': expense.description
        })
    
    # Sort transactions by date (descending)
    transactions.sort(key=lambda x: x['date'], reverse=True)

    for t in transactions:
        writer.writerow([t['date'], t['type'], t['category'], t['amount'], t['description']])

    return response

@login_required(login_url='login')
def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expense_report.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Title
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Expense Tracker Report", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    # Data
    incomes = Income.objects.filter(user=request.user)
    expenses = Expense.objects.filter(user=request.user)

    transactions = []
    for income in incomes:
        transactions.append([
            str(income.date),
            'Income',
            income.source.name if income.source else 'N/A',
            str(income.amount),
            income.description or ''
        ])
    
    for expense in expenses:
        transactions.append([
            str(expense.date),
            'Expense',
            expense.category.name if expense.category else 'N/A',
            str(expense.amount),
            expense.description or ''
        ])
    
    # Sort by date
    transactions.sort(key=lambda x: x[0], reverse=True)

    # Table Header
    data = [['Date', 'Type', 'Category/Source', 'Amount', 'Description']] + transactions

    # Table Style
    table = Table(data, colWidths=[1.0*inch, 0.8*inch, 1.5*inch, 1.0*inch, 2.0*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

@login_required(login_url='login')
def dashboard(request):
    incomes = Income.objects.filter(user=request.user).order_by('-date')[:5]
    expenses = Expense.objects.filter(user=request.user).order_by('-date')[:5]
    
    total_income = sum(income.amount for income in Income.objects.filter(user=request.user))
    total_expense = sum(expense.amount for expense in Expense.objects.filter(user=request.user))
    balance = total_income - total_expense

    # AI Suggestion (Simple Prediction)
    # Predict next month's expense based on average of last 3 months
    today = datetime.date.today()
    three_months_ago = today - datetime.timedelta(days=90)
    past_expenses = Expense.objects.filter(user=request.user, date__gte=three_months_ago)
    
    predicted_expense = 0
    if past_expenses.exists():
        total_past_expense = sum(e.amount for e in past_expenses)
        predicted_expense = total_past_expense / 3
    all_expenses = Expense.objects.filter(user=request.user)
    cat_sums = {}
    for e in all_expenses:
        name = e.category.name if e.category else 'Uncategorized'
        cat_sums[name] = cat_sums.get(name, 0) + float(e.amount)
    category_labels = list(cat_sums.keys())
    category_values = [cat_sums[k] for k in category_labels]
    months_labels = []
    monthly_expenses = []
    monthly_incomes = []
    today = datetime.date.today()
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        start = datetime.date(y, m, 1)
        s, e = _month_bounds(start)
        months_labels.append(start.strftime('%b %Y'))
        monthly_expenses.append(float(sum(x.amount for x in Expense.objects.filter(user=request.user, date__gte=s, date__lte=e))))
        monthly_incomes.append(float(sum(x.amount for x in Income.objects.filter(user=request.user, date__gte=s, date__lte=e))))

    context = {
        'recent_incomes': incomes,
        'recent_expenses': expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'predicted_expense': round(predicted_expense, 2),
        'category_labels_json': json.dumps(category_labels),
        'category_values_json': json.dumps(category_values),
        'months_labels_json': json.dumps(months_labels),
        'monthly_expenses_json': json.dumps(monthly_expenses),
        'monthly_incomes_json': json.dumps(monthly_incomes),
    }
    return render(request, 'finance/dashboard.html', context)

@login_required(login_url='login')
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, 'Income added successfully!')
            return redirect('dashboard')
    else:
        form = IncomeForm()
        form.fields['source'].queryset = Source.objects.filter(Q(user=request.user) | Q(user__isnull=True))
    return render(request, 'finance/add_income.html', {'form': form})

@login_required(login_url='login')
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            
            # Check Budget
            if expense.category:
                budgets = Budget.objects.filter(
                    user=request.user, 
                    category=expense.category,
                    start_date__lte=expense.date,
                    end_date__gte=expense.date
                )
                for budget in budgets:
                    total_cat_expenses = sum(e.amount for e in Expense.objects.filter(
                        user=request.user,
                        category=expense.category,
                        date__gte=budget.start_date,
                        date__lte=budget.end_date
                    ))
                    if total_cat_expenses > budget.amount:
                        messages.warning(request, f'Alert: You have exceeded your budget for {expense.category.name}!')
                        
                        # Send Email Alert
                        if request.user.email:
                            subject = f'Budget Exceeded Alert: {expense.category.name}'
                            message = f'''Dear {request.user.username},

You have exceeded your budget for {expense.category.name}.

Budget Limit: {budget.amount}
Total Expenses: {total_cat_expenses}

Please review your expenses.

Best regards,
Budget Tracker App
'''
                            try:
                                send_mail(
                                    subject,
                                    message,
                                    'admin@budgettracker.com',
                                    [request.user.email],
                                    fail_silently=False,
                                )
                            except Exception as e:
                                print(f"Error sending email: {e}")
            
            messages.success(request, 'Expense added successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm() 
        form.fields['category'].queryset = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True))

    return render(request, 'finance/add_expense.html', {'form': form})

@login_required(login_url='login')
def set_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            today = datetime.date.today()
            start, end = _month_bounds(today)
            budget.start_date = start
            budget.end_date = end
            budget.save()
            messages.success(request, 'Budget set successfully!')
            return redirect('dashboard')
    else:
        form = BudgetForm(user=request.user)
    return render(request, 'finance/set_budget.html', {'form': form})

@login_required(login_url='login')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('add_expense') # Redirect back to add expense usually
    else:
        form = CategoryForm()
    return render(request, 'finance/add_category.html', {'form': form})

@login_required(login_url='login')
def add_source(request):
    if request.method == 'POST':
        form = SourceForm(request.POST)
        if form.is_valid():
            source = form.save(commit=False)
            source.user = request.user
            source.save()
            messages.success(request, 'Source added successfully!')
            return redirect('add_income') # Redirect back to add income usually
    else:
        form = SourceForm()
    return render(request, 'finance/add_source.html', {'form': form})

@login_required(login_url='login')
def list_budgets(request):
    budgets = Budget.objects.filter(user=request.user).select_related('category').order_by('-start_date')
    return render(request, 'finance/budgets_list.html', {'budgets': budgets})

@login_required(login_url='login')
def edit_budget(request, pk):
    budget = Budget.objects.filter(user=request.user, pk=pk).first()
    if not budget:
        messages.error(request, 'Budget not found.')
        return redirect('list_budgets')
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated successfully!')
            return redirect('list_budgets')
    else:
        form = BudgetForm(instance=budget, user=request.user)
    return render(request, 'finance/edit_budget.html', {'form': form, 'budget': budget})

@login_required(login_url='login')
def delete_budget(request, pk):
    budget = Budget.objects.filter(user=request.user, pk=pk).first()
    if not budget:
        messages.error(request, 'Budget not found.')
        return redirect('list_budgets')
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully!')
        return redirect('list_budgets')
    return redirect('list_budgets')
@login_required(login_url='login')
def list_incomes(request):
    incomes = Income.objects.filter(user=request.user).select_related('source').order_by('-date')
    return render(request, 'finance/incomes_list.html', {'incomes': incomes})

@login_required(login_url='login')
def edit_income(request, pk):
    income = Income.objects.filter(user=request.user, pk=pk).first()
    if not income:
        messages.error(request, 'Income not found.')
        return redirect('list_incomes')
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income updated successfully!')
            return redirect('list_incomes')
    else:
        form = IncomeForm(instance=income)
        form.fields['source'].queryset = Source.objects.filter(Q(user=request.user) | Q(user__isnull=True))
    return render(request, 'finance/edit_income.html', {'form': form, 'income': income})

@login_required(login_url='login')
def list_expenses(request):
    expenses = Expense.objects.filter(user=request.user).select_related('category').order_by('-date')
    return render(request, 'finance/expenses_list.html', {'expenses': expenses})

@login_required(login_url='login')
def edit_expense(request, pk):
    expense = Expense.objects.filter(user=request.user, pk=pk).first()
    if not expense:
        messages.error(request, 'Expense not found.')
        return redirect('list_expenses')
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('list_expenses')
    else:
        form = ExpenseForm(instance=expense)
        form.fields['category'].queryset = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True))
    return render(request, 'finance/edit_expense.html', {'form': form, 'expense': expense})

@login_required(login_url='login')
def delete_income(request, pk):
    income = Income.objects.filter(user=request.user, pk=pk).first()
    if not income:
        messages.error(request, 'Income not found.')
        return redirect('list_incomes')
    if request.method == 'POST':
        income.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Income deleted successfully!')
    return redirect('list_incomes')

@login_required(login_url='login')
def delete_expense(request, pk):
    expense = Expense.objects.filter(user=request.user, pk=pk).first()
    if not expense:
        messages.error(request, 'Expense not found.')
        return redirect('list_expenses')
    if request.method == 'POST':
        expense.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Expense deleted successfully!')
    return redirect('list_expenses')

@login_required(login_url='login')
def delete_source(request, pk):
    source = Source.objects.filter(user=request.user, pk=pk).first()
    if not source:
        messages.error(request, 'Only your own Sources can be deleted.')
        return redirect('list_sources')
    if request.method == 'POST':
        source.delete()
        messages.success(request, 'Source deleted successfully!')
    return redirect('list_sources')

@login_required(login_url='login')
def delete_category(request, pk):
    category = Category.objects.filter(user=request.user, pk=pk).first()
    if not category:
        messages.error(request, 'Only your own Categories can be deleted.')
        return redirect('list_categories')
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
    return redirect('list_categories')
@login_required(login_url='login')
def list_sources(request):
    sources = Source.objects.filter(Q(user=request.user) | Q(user__isnull=True)).order_by('name')
    return render(request, 'finance/sources_list.html', {'sources': sources})

@login_required(login_url='login')
def edit_source(request, pk):
    source = Source.objects.filter(user=request.user, pk=pk).first()
    if not source:
        messages.error(request, 'Only your own Sources can be edited.')
        return redirect('list_sources')
    if request.method == 'POST':
        form = SourceForm(request.POST, instance=source)
        if form.is_valid():
            form.save()
            messages.success(request, 'Source updated successfully!')
            return redirect('list_sources')
    else:
        form = SourceForm(instance=source)
    return render(request, 'finance/edit_source.html', {'form': form, 'source': source})

@login_required(login_url='login')
def list_categories(request):
    categories = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True)).order_by('name')
    return render(request, 'finance/categories_list.html', {'categories': categories})

@login_required(login_url='login')
def edit_category(request, pk):
    category = Category.objects.filter(user=request.user, pk=pk).first()
    if not category:
        messages.error(request, 'Only your own Categories can be edited.')
        return redirect('list_categories')
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('list_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'finance/edit_category.html', {'form': form, 'category': category})
