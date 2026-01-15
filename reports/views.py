from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse, HttpResponse
from finance.models import Expense, Income, Budget, Category, Source
import csv
import datetime
from django.utils import timezone

@login_required
def dashboard_view(request):
    # Budget vs Actuals
    today = datetime.date.today()
    active_budgets = Budget.objects.filter(user=request.user, start_date__lte=today, end_date__gte=today)
    
    budget_data = []
    for budget in active_budgets:
        expenses = Expense.objects.filter(
            user=request.user,
            category=budget.category,
            date__range=[budget.start_date, budget.end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        percent = (expenses / budget.amount) * 100 if budget.amount > 0 else 0
        
        budget_data.append({
            'category': budget.category.name if budget.category else 'Uncategorized',
            'limit': budget.amount,
            'spent': expenses,
            'remaining': budget.amount - expenses,
            'over_amount': expenses - budget.amount if expenses > budget.amount else 0,
            'percent': min(percent, 100),
            'is_exceeded': expenses > budget.amount,
            'start_date': budget.start_date,
            'end_date': budget.end_date
        })

    # Detailed Expense Breakdown
    expense_breakdown = Expense.objects.filter(user=request.user).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    # Detailed Income Breakdown
    income_breakdown = Income.objects.filter(user=request.user).values('source__name').annotate(total=Sum('amount')).order_by('-total')

    context = {
        'budget_data': budget_data,
        'expense_breakdown': expense_breakdown,
        'income_breakdown': income_breakdown,
    }
    return render(request, 'reports/index.html', context)

@login_required
def expense_category_data(request):
    expenses = Expense.objects.filter(user=request.user).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    labels = [e['category__name'] for e in expenses]
    data = [float(e['total']) for e in expenses]
    return JsonResponse({'labels': labels, 'data': data})

@login_required
def income_expense_data(request):
    # Get last 6 months data
    today = datetime.date.today()
    six_months_ago = today - datetime.timedelta(days=180)
    
    expenses = Expense.objects.filter(user=request.user, date__gte=six_months_ago)\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('amount'))\
        .order_by('month')
        
    incomes = Income.objects.filter(user=request.user, date__gte=six_months_ago)\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('amount'))\
        .order_by('month')
    
    # Merge data
    data_map = {}
    for e in expenses:
        month = e['month'].strftime('%Y-%m')
        if month not in data_map:
            data_map[month] = {'expense': 0, 'income': 0}
        data_map[month]['expense'] = float(e['total'])
        
    for i in incomes:
        month = i['month'].strftime('%Y-%m')
        if month not in data_map:
            data_map[month] = {'expense': 0, 'income': 0}
        data_map[month]['income'] = float(i['total'])
        
    months = sorted(data_map.keys())
    expense_data = [data_map[m]['expense'] for m in months]
    income_data = [data_map[m]['income'] for m in months]
    
    return JsonResponse({
        'labels': months,
        'expense': expense_data,
        'income': income_data
    })

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Type', 'Date', 'Category/Source', 'Description', 'Amount'])
    
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    for e in expenses:
        writer.writerow(['Expense', e.date, e.category.name if e.category else 'Uncategorized', e.description, e.amount])
        
    incomes = Income.objects.filter(user=request.user).order_by('-date')
    for i in incomes:
        writer.writerow(['Income', i.date, i.source.name if i.source else 'Uncategorized', i.description, i.amount])
        
    return response
