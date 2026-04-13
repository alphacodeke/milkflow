import csv
import io
import json
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from .models import Farm, Cow, MilkRecord, HealthEvent, FinancialTransaction, ScheduledTask, Employee
from .forms import (RegisterForm, LoginForm, CowForm, MilkRecordForm, HealthEventForm,
                     FinancialTransactionForm, ScheduledTaskForm, EmployeeForm, FarmForm, DateRangeForm)


# ─────────────────────── LANDING ───────────────────────
def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')


# ─────────────────────── AUTH ───────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to MilkFlow! Your farm account is ready.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


# ─────────────────────── DASHBOARD ───────────────────────
@login_required
def dashboard(request):
    user = request.user
    today = date.today()

    # Core metrics
    total_cows = Cow.objects.filter(user=user, status__in=['active', 'pregnant']).count()
    today_milk = MilkRecord.objects.filter(user=user, record_date=today).aggregate(
        total=Sum('am_yield') + Sum('pm_yield') if MilkRecord.objects.filter(user=user, record_date=today).exists() else Sum('am_yield')
    )
    # Compute today's milk properly
    today_records = MilkRecord.objects.filter(user=user, record_date=today)
    today_milk_total = sum(r.total_yield for r in today_records)

    # Running balance
    income_total = FinancialTransaction.objects.filter(
        user=user, transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expense_total = FinancialTransaction.objects.filter(
        user=user, transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    balance = income_total - expense_total

    # Upcoming tasks
    upcoming_tasks = ScheduledTask.objects.filter(
        user=user, status='pending', due_date__gte=today
    ).select_related('cow').order_by('due_date')[:5]

    overdue_tasks_count = ScheduledTask.objects.filter(
        user=user, status='pending', due_date__lt=today
    ).count()

    # 7-day milk trend for Chart.js
    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        trend_labels.append(d.strftime('%b %d'))
        day_records = MilkRecord.objects.filter(user=user, record_date=d)
        day_total = sum(r.total_yield for r in day_records)
        trend_data.append(float(day_total))

    # Recent transactions
    recent_transactions = FinancialTransaction.objects.filter(user=user).order_by('-transaction_date', '-created_at')[:5]

    # Recent health events
    recent_health = HealthEvent.objects.filter(user=user).select_related('cow').order_by('-event_date')[:3]

    # Herd breakdown
    herd_status = {
        'active': Cow.objects.filter(user=user, status='active').count(),
        'dry': Cow.objects.filter(user=user, status='dry').count(),
        'pregnant': Cow.objects.filter(user=user, status='pregnant').count(),
    }

    try:
        farm = user.farm
    except Farm.DoesNotExist:
        farm = Farm.objects.create(user=user, name=f"{user.username}'s Farm")

    context = {
        'farm': farm,
        'total_cows': total_cows,
        'today_milk': today_milk_total,
        'balance': balance,
        'income_total': income_total,
        'expense_total': expense_total,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks_count': overdue_tasks_count,
        'trend_labels': json.dumps(trend_labels),
        'trend_data': json.dumps(trend_data),
        'recent_transactions': recent_transactions,
        'recent_health': recent_health,
        'herd_status': herd_status,
        'today': today,
    }
    return render(request, 'core/dashboard.html', context)


# ─────────────────────── COWS ───────────────────────
@login_required
def cow_list(request):
    qs = Cow.objects.filter(user=request.user)
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if search:
        qs = qs.filter(Q(tag_number__icontains=search) | Q(name__icontains=search) | Q(breed__icontains=search))
    if status:
        qs = qs.filter(status=status)
    total = qs.count()
    context = {'cows': qs, 'search': search, 'status_filter': status, 'total': total}
    return render(request, 'core/cow_list.html', context)


@login_required
def cow_add(request):
    if request.method == 'POST':
        form = CowForm(request.POST)
        if form.is_valid():
            cow = form.save(commit=False)
            cow.user = request.user
            cow.save()
            messages.success(request, f'Cow {cow.tag_number} added successfully!')
            return redirect('cow_list')
    else:
        form = CowForm()
    return render(request, 'core/cow_form.html', {'form': form, 'action': 'Add', 'title': 'Add New Cow'})


@login_required
def cow_edit(request, pk):
    cow = get_object_or_404(Cow, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CowForm(request.POST, instance=cow)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cow {cow.tag_number} updated!')
            return redirect('cow_list')
    else:
        form = CowForm(instance=cow)
    return render(request, 'core/cow_form.html', {'form': form, 'cow': cow, 'action': 'Edit', 'title': f'Edit {cow}'})


@login_required
def cow_detail(request, pk):
    cow = get_object_or_404(Cow, pk=pk, user=request.user)
    recent_milk = MilkRecord.objects.filter(cow=cow).order_by('-record_date')[:14]
    health_events = HealthEvent.objects.filter(cow=cow).order_by('-event_date')[:10]
    tasks = ScheduledTask.objects.filter(cow=cow, status='pending').order_by('due_date')[:5]
    total_milk_30 = sum(r.total_yield for r in MilkRecord.objects.filter(
        cow=cow, record_date__gte=date.today() - timedelta(days=30)
    ))
    context = {'cow': cow, 'recent_milk': recent_milk, 'health_events': health_events,
               'tasks': tasks, 'total_milk_30': total_milk_30}
    return render(request, 'core/cow_detail.html', context)


@login_required
@require_POST
def cow_delete(request, pk):
    cow = get_object_or_404(Cow, pk=pk, user=request.user)
    tag = cow.tag_number
    cow.delete()
    messages.success(request, f'Cow {tag} deleted.')
    return redirect('cow_list')


# ─────────────────────── MILK RECORDS ───────────────────────
@login_required
def milk_list(request):
    qs = MilkRecord.objects.filter(user=request.user).select_related('cow')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    cow_filter = request.GET.get('cow', '')
    if date_from:
        qs = qs.filter(record_date__gte=date_from)
    if date_to:
        qs = qs.filter(record_date__lte=date_to)
    if cow_filter:
        qs = qs.filter(cow_id=cow_filter)

    total_yield = sum(r.total_yield for r in qs)
    cow_list_qs = Cow.objects.filter(user=request.user).order_by('tag_number')

    # Paginate manually (simple)
    page = int(request.GET.get('page', 1))
    per_page = 25
    total_count = qs.count()
    records = qs[(page-1)*per_page: page*per_page]
    total_pages = (total_count + per_page - 1) // per_page

    context = {
        'records': records, 'total_yield': total_yield,
        'date_from': date_from, 'date_to': date_to,
        'cow_filter': cow_filter, 'cow_list': cow_list_qs,
        'page': page, 'total_pages': total_pages, 'total_count': total_count,
    }
    return render(request, 'core/milk_list.html', context)


@login_required
def milk_add(request):
    if request.method == 'POST':
        form = MilkRecordForm(request.POST, user=request.user)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            messages.success(request, f'Milk recorded: {record.total_yield}L total.')
            return redirect('milk_list')
    else:
        form = MilkRecordForm(user=request.user)
    return render(request, 'core/milk_form.html', {'form': form, 'action': 'Add', 'title': 'Record Milk Yield'})


@login_required
def milk_edit(request, pk):
    record = get_object_or_404(MilkRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MilkRecordForm(request.POST, instance=record, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Milk record updated!')
            return redirect('milk_list')
    else:
        form = MilkRecordForm(instance=record, user=request.user)
    return render(request, 'core/milk_form.html', {'form': form, 'record': record, 'action': 'Edit', 'title': 'Edit Milk Record'})


@login_required
@require_POST
def milk_delete(request, pk):
    record = get_object_or_404(MilkRecord, pk=pk, user=request.user)
    record.delete()
    messages.success(request, 'Milk record deleted.')
    return redirect('milk_list')


# ─────────────────────── FINANCES ───────────────────────
@login_required
def finance_list(request):
    qs = FinancialTransaction.objects.filter(user=request.user)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    txn_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    if date_from:
        qs = qs.filter(transaction_date__gte=date_from)
    if date_to:
        qs = qs.filter(transaction_date__lte=date_to)
    if txn_type:
        qs = qs.filter(transaction_type=txn_type)
    if category:
        qs = qs.filter(category=category)

    # Running balance (all time)
    all_txns = FinancialTransaction.objects.filter(user=request.user).order_by('transaction_date', 'created_at')
    running = Decimal('0')
    running_balance_map = {}
    for t in all_txns:
        if t.transaction_type == 'income':
            running += t.amount
        else:
            running -= t.amount
        running_balance_map[t.pk] = running

    total_income = FinancialTransaction.objects.filter(user=request.user, transaction_type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    total_expense = FinancialTransaction.objects.filter(user=request.user, transaction_type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    balance = total_income - total_expense

    income_categories = FinancialTransaction.INCOME_CATEGORIES
    expense_categories = FinancialTransaction.EXPENSE_CATEGORIES

    context = {
        'transactions': qs, 'running_balance_map': running_balance_map,
        'total_income': total_income, 'total_expense': total_expense, 'balance': balance,
        'date_from': date_from, 'date_to': date_to, 'type_filter': txn_type,
        'category_filter': category,
        'income_categories': income_categories, 'expense_categories': expense_categories,
    }
    return render(request, 'core/finance_list.html', context)


@login_required
def finance_add(request):
    if request.method == 'POST':
        form = FinancialTransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.user = request.user
            txn.save()
            messages.success(request, f'{txn.get_transaction_type_display()} of KES {txn.amount} recorded!')
            return redirect('finance_list')
    else:
        form = FinancialTransactionForm()
    income_cats = FinancialTransaction.INCOME_CATEGORIES
    expense_cats = FinancialTransaction.EXPENSE_CATEGORIES
    return render(request, 'core/finance_form.html', {
        'form': form, 'title': 'Add Transaction',
        'income_cats': json.dumps(dict(income_cats)),
        'expense_cats': json.dumps(dict(expense_cats)),
    })


@login_required
@require_POST
def finance_delete(request, pk):
    txn = get_object_or_404(FinancialTransaction, pk=pk, user=request.user)
    txn.delete()
    messages.success(request, 'Transaction deleted.')
    return redirect('finance_list')


# ─────────────────────── HEALTH ───────────────────────
@login_required
def health_list(request):
    qs = HealthEvent.objects.filter(user=request.user).select_related('cow')
    status_filter = request.GET.get('status', '')
    event_type = request.GET.get('type', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if event_type:
        qs = qs.filter(event_type=event_type)
    context = {'events': qs, 'status_filter': status_filter, 'type_filter': event_type,
               'event_types': HealthEvent.EVENT_TYPES, 'status_choices': HealthEvent.STATUS_CHOICES}
    return render(request, 'core/health_list.html', context)


@login_required
def health_add(request):
    if request.method == 'POST':
        form = HealthEventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            messages.success(request, 'Health event recorded!')
            return redirect('health_list')
    else:
        form = HealthEventForm(user=request.user)
    return render(request, 'core/health_form.html', {'form': form, 'title': 'Record Health Event'})


@login_required
def health_edit(request, pk):
    event = get_object_or_404(HealthEvent, pk=pk, user=request.user)
    if request.method == 'POST':
        form = HealthEventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Health event updated!')
            return redirect('health_list')
    else:
        form = HealthEventForm(instance=event, user=request.user)
    return render(request, 'core/health_form.html', {'form': form, 'event': event, 'title': 'Edit Health Event'})


@login_required
@require_POST
def health_delete(request, pk):
    event = get_object_or_404(HealthEvent, pk=pk, user=request.user)
    event.delete()
    messages.success(request, 'Health event deleted.')
    return redirect('health_list')


# ─────────────────────── TASKS ───────────────────────
@login_required
def task_list(request):
    qs = ScheduledTask.objects.filter(user=request.user).select_related('cow')
    status_filter = request.GET.get('status', 'pending')
    if status_filter and status_filter != 'all':
        qs = qs.filter(status=status_filter)
    today = date.today()
    overdue = qs.filter(status='pending', due_date__lt=today)
    context = {'tasks': qs, 'status_filter': status_filter, 'today': today,
               'overdue_count': overdue.count()}
    return render(request, 'core/task_list.html', context)


@login_required
def task_add(request):
    if request.method == 'POST':
        form = ScheduledTaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" scheduled for {task.due_date}!')
            return redirect('task_list')
    else:
        form = ScheduledTaskForm(user=request.user)
    return render(request, 'core/task_form.html', {'form': form, 'title': 'Schedule New Task'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(ScheduledTask, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ScheduledTaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated!')
            return redirect('task_list')
    else:
        form = ScheduledTaskForm(instance=task, user=request.user)
    return render(request, 'core/task_form.html', {'form': form, 'task': task, 'title': 'Edit Task'})


@login_required
@require_POST
def task_complete(request, pk):
    task = get_object_or_404(ScheduledTask, pk=pk, user=request.user)
    task.status = 'completed'
    task.save()
    messages.success(request, f'Task "{task.title}" marked as completed!')
    return redirect('task_list')


@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(ScheduledTask, pk=pk, user=request.user)
    task.delete()
    messages.success(request, 'Task deleted.')
    return redirect('task_list')


# ─────────────────────── EMPLOYEES ───────────────────────
@login_required
def employee_list(request):
    employees = Employee.objects.filter(user=request.user)
    total_salary = employees.filter(status='active').aggregate(t=Sum('monthly_salary'))['t'] or Decimal('0')
    return render(request, 'core/employee_list.html', {'employees': employees, 'total_salary': total_salary})


@login_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            emp = form.save(commit=False)
            emp.user = request.user
            emp.save()
            messages.success(request, f'Employee {emp.full_name} added!')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'core/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_edit(request, pk):
    emp = get_object_or_404(Employee, pk=pk, user=request.user)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=emp)
        if form.is_valid():
            form.save()
            messages.success(request, f'{emp.full_name} updated!')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'core/employee_form.html', {'form': form, 'emp': emp, 'title': 'Edit Employee'})


@login_required
@require_POST
def employee_delete(request, pk):
    emp = get_object_or_404(Employee, pk=pk, user=request.user)
    name = emp.full_name
    emp.delete()
    messages.success(request, f'{name} removed.')
    return redirect('employee_list')


# ─────────────────────── REPORTS ───────────────────────
@login_required
def reports(request):
    try:
        farm = request.user.farm
    except Farm.DoesNotExist:
        farm = None
    return render(request, 'core/reports.html', {'farm': farm})


@login_required
def report_milk_pdf(request):
    user = request.user
    date_from = request.GET.get('date_from', (date.today() - timedelta(days=30)).isoformat())
    date_to = request.GET.get('date_to', date.today().isoformat())

    records = MilkRecord.objects.filter(
        user=user, record_date__gte=date_from, record_date__lte=date_to
    ).select_related('cow').order_by('-record_date')

    try:
        farm_name = user.farm.name
    except Farm.DoesNotExist:
        farm_name = f"{user.username}'s Farm"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    green = rl_colors.HexColor('#2E7D32')
    amber = rl_colors.HexColor('#F9A825')
    grey = rl_colors.HexColor('#666666')

    title_style = ParagraphStyle('mfTitle', parent=styles['Title'], textColor=green, fontSize=22, spaceAfter=4)
    sub_style = ParagraphStyle('mfSub', parent=styles['Normal'], textColor=grey, fontSize=10)

    story = []
    story.append(Paragraph(f"MilkFlow — {farm_name}", title_style))
    story.append(Paragraph(f"Milk Production Report  |  {date_from} to {date_to}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=green))
    story.append(Spacer(1, 0.4*cm))

    total_yield = sum(r.total_yield for r in records)
    story.append(Paragraph(
        f"Total Records: <b>{records.count()}</b>  &nbsp;&nbsp;|&nbsp;&nbsp;  Total Yield: <b>{total_yield:.1f} L</b>  &nbsp;&nbsp;|&nbsp;&nbsp;  Generated: <b>{date.today()}</b>",
        sub_style
    ))
    story.append(Spacer(1, 0.5*cm))

    if records.exists():
        data = [['Date', 'Cow Tag', 'Name', 'AM (L)', 'PM (L)', 'Total (L)']]
        for r in records:
            data.append([
                str(r.record_date),
                r.cow.tag_number if r.cow else '—',
                r.cow.name if r.cow and r.cow.name else '—',
                f"{float(r.am_yield):.1f}",
                f"{float(r.pm_yield):.1f}",
                f"{float(r.total_yield):.1f}",
            ])
        data.append(['', '', 'GRAND TOTAL', '', '', f"{float(total_yield):.1f} L"])

        tbl = Table(data, colWidths=[2.8*cm, 2.5*cm, 3.5*cm, 2.5*cm, 2.5*cm, 2.8*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), green),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [rl_colors.HexColor('#F5F5F0'), rl_colors.white]),
            ('BACKGROUND', (0, -1), (-1, -1), amber),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.4, rl_colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
    else:
        story.append(Paragraph("No milk records found for this period.", styles['Normal']))

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Generated by MilkFlow Dairy Management System", sub_style))

    doc.build(story)
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="milk_report_{date_from}_{date_to}.pdf"'
    return response


@login_required
def report_finance_pdf(request):
    user = request.user
    date_from = request.GET.get('date_from', (date.today() - timedelta(days=30)).isoformat())
    date_to = request.GET.get('date_to', date.today().isoformat())

    transactions = FinancialTransaction.objects.filter(
        user=user, transaction_date__gte=date_from, transaction_date__lte=date_to
    ).order_by('transaction_date', 'created_at')

    try:
        farm_name = user.farm.name
    except Farm.DoesNotExist:
        farm_name = f"{user.username}'s Farm"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    green = rl_colors.HexColor('#2E7D32')
    amber = rl_colors.HexColor('#F9A825')
    red = rl_colors.HexColor('#C62828')
    grey = rl_colors.HexColor('#666666')

    title_style = ParagraphStyle('mfTitle', parent=styles['Title'], textColor=green, fontSize=22, spaceAfter=4)
    sub_style = ParagraphStyle('mfSub', parent=styles['Normal'], textColor=grey, fontSize=10)

    story = []
    story.append(Paragraph(f"MilkFlow — {farm_name}", title_style))
    story.append(Paragraph(f"Financial Report  |  {date_from} to {date_to}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=green))
    story.append(Spacer(1, 0.4*cm))

    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expense = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    net = total_income - total_expense

    story.append(Paragraph(
        f"Total Income: <b>KES {float(total_income):,.2f}</b>  &nbsp;|&nbsp;  "
        f"Total Expenses: <b>KES {float(total_expense):,.2f}</b>  &nbsp;|&nbsp;  "
        f"Net Balance: <b>KES {float(net):,.2f}</b>",
        sub_style
    ))
    story.append(Spacer(1, 0.5*cm))

    if transactions.exists():
        running = Decimal('0')
        data = [['Date', 'Type', 'Category', 'Description', 'Amount (KES)', 'Balance (KES)']]
        for t in transactions:
            if t.transaction_type == 'income':
                running += t.amount
                amount_str = f"+{float(t.amount):,.2f}"
            else:
                running -= t.amount
                amount_str = f"-{float(t.amount):,.2f}"
            data.append([
                str(t.transaction_date),
                t.get_transaction_type_display(),
                t.get_category_display_name(),
                (t.description or '')[:25],
                amount_str,
                f"{float(running):,.2f}",
            ])

        tbl = Table(data, colWidths=[2.3*cm, 2*cm, 3*cm, 3.5*cm, 3*cm, 3*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), green),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [rl_colors.HexColor('#F5F5F0'), rl_colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.4, rl_colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Generated by MilkFlow Dairy Management System", sub_style))
    doc.build(story)
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="finance_report_{date_from}_{date_to}.pdf"'
    return response


@login_required
def report_health_pdf(request):
    user = request.user
    date_from = request.GET.get('date_from', (date.today() - timedelta(days=90)).isoformat())
    date_to = request.GET.get('date_to', date.today().isoformat())

    events = HealthEvent.objects.filter(
        user=user, event_date__gte=date_from, event_date__lte=date_to
    ).select_related('cow').order_by('-event_date')

    try:
        farm_name = user.farm.name
    except Farm.DoesNotExist:
        farm_name = f"{user.username}'s Farm"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    green = rl_colors.HexColor('#2E7D32')
    grey = rl_colors.HexColor('#666666')
    title_style = ParagraphStyle('T', parent=styles['Title'], textColor=green, fontSize=22)
    sub_style = ParagraphStyle('S', parent=styles['Normal'], textColor=grey, fontSize=10)

    story = []
    story.append(Paragraph(f"MilkFlow — {farm_name}", title_style))
    story.append(Paragraph(f"Health Events Report  |  {date_from} to {date_to}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=green))
    story.append(Spacer(1, 0.5*cm))

    total_cost = sum(e.cost for e in events)
    story.append(Paragraph(f"Total Events: <b>{events.count()}</b>  |  Total Cost: <b>KES {float(total_cost):,.2f}</b>", sub_style))
    story.append(Spacer(1, 0.4*cm))

    if events.exists():
        data = [['Date', 'Cow', 'Event Type', 'Status', 'Vet', 'Cost (KES)']]
        for e in events:
            data.append([
                str(e.event_date),
                e.cow.tag_number if e.cow else 'Herd',
                e.get_event_type_display(),
                e.get_status_display(),
                e.vet_name or '—',
                f"{float(e.cost):,.2f}",
            ])
        tbl = Table(data, colWidths=[2.5*cm, 2*cm, 3.5*cm, 2.5*cm, 3*cm, 3*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), green),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [rl_colors.HexColor('#F5F5F0'), rl_colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.4, rl_colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Generated by MilkFlow Dairy Management System", sub_style))
    doc.build(story)
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="health_report_{date_from}_{date_to}.pdf"'
    return response


@login_required
def report_milk_csv(request):
    user = request.user
    date_from = request.GET.get('date_from', (date.today() - timedelta(days=30)).isoformat())
    date_to = request.GET.get('date_to', date.today().isoformat())

    records = MilkRecord.objects.filter(
        user=user, record_date__gte=date_from, record_date__lte=date_to
    ).select_related('cow').order_by('-record_date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="milk_records_{date_from}_{date_to}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Cow Tag', 'Cow Name', 'Breed', 'AM Yield (L)', 'PM Yield (L)', 'Total Yield (L)', 'Notes'])
    for r in records:
        writer.writerow([
            r.record_date,
            r.cow.tag_number if r.cow else '',
            r.cow.name if r.cow else '',
            r.cow.breed if r.cow else '',
            float(r.am_yield), float(r.pm_yield), float(r.total_yield),
            r.notes or '',
        ])
    return response


@login_required
def report_finance_csv(request):
    user = request.user
    date_from = request.GET.get('date_from', (date.today() - timedelta(days=30)).isoformat())
    date_to = request.GET.get('date_to', date.today().isoformat())

    transactions = FinancialTransaction.objects.filter(
        user=user, transaction_date__gte=date_from, transaction_date__lte=date_to
    ).order_by('transaction_date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transactions_{date_from}_{date_to}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Category', 'Description', 'Amount (KES)', 'Reference'])
    for t in transactions:
        writer.writerow([
            t.transaction_date, t.get_transaction_type_display(),
            t.get_category_display_name(), t.description,
            float(t.amount), t.reference,
        ])
    return response


# ─────────────────────── API (AJAX) ───────────────────────
@login_required
def api_milk_trend(request):
    days = int(request.GET.get('days', 30))
    today = date.today()
    data = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        day_records = MilkRecord.objects.filter(user=request.user, record_date=d)
        total = sum(r.total_yield for r in day_records)
        data.append({'date': d.strftime('%b %d'), 'yield': float(total)})
    return JsonResponse(data, safe=False)


# ─────────────────────── FARM PROFILE ───────────────────────
@login_required
def farm_profile(request):
    try:
        farm = request.user.farm
    except Farm.DoesNotExist:
        farm = Farm(user=request.user)
    if request.method == 'POST':
        form = FarmForm(request.POST, instance=farm)
        if form.is_valid():
            f = form.save(commit=False)
            f.user = request.user
            f.save()
            messages.success(request, 'Farm profile updated!')
            return redirect('farm_profile')
    else:
        form = FarmForm(instance=farm)
    return render(request, 'core/farm_profile.html', {'form': form, 'farm': farm})
