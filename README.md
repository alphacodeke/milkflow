# 🐄 MilkFlow — Dairy Farm Management System
![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-Backend-green?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-Framework-darkgreen?logo=django&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Database-blue?logo=mysql&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-Markup-orange?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-Styling-blue?logo=css3&logoColor=white)

A complete Django web application for dairy farm management.

## Tech Stack
- **Backend**: Django 4.2+ with SQLite3
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js (CDN)
- **PDF Reports**: ReportLab
- **Auth**: Django built-in authentication

## Models
| Model | Description |
|-------|-------------|
| `Farm` | Farm profile linked to user |
| `Cow` | Individual cow records with breed, status, age |
| `MilkRecord` | AM/PM daily milk yields per cow |
| `HealthEvent` | Vaccinations, treatments, deworming |
| `FinancialTransaction` | Income & expense ledger |
| `ScheduledTask` | Task reminders with due dates & priority |
| `Employee` | Farm worker records |

## Quick Setup

### 1. Install dependencies
```bash
pip install django reportlab
```

### 2. Run migrations
```bash
cd milkflow_django
python manage.py migrate
```

### 3. (Optional) Create a superuser for Django admin
```bash
python manage.py createsuperuser
```

### 4. Start the development server
```bash
python manage.py runserver
```

### 5. Open in browser
```
http://127.0.0.1:8000/
```

## Features

### Dashboard
- Total active cows, today's milk yield, running balance, overdue tasks
- 7-day milk production trend chart (Chart.js)
- Upcoming tasks list with overdue warnings
- Recent transactions and health events
- Quick action buttons

### Cow Management
- Full CRUD with search and status filtering
- Breeds: Friesian, Ayrshire, Jersey, Guernsey, Holstein, Crossbreed
- Age auto-calculation from date of birth
- Individual cow detail page with milk history and health events

### Milk Recording
- AM + PM yield entry with live daily total calculation
- Per-cow or general herd records
- Filter by date range and cow
- Pagination for large datasets

### Financial Ledger
- Income categories: Milk Sales, Animal Sales, Manure, Grants, Other
- Expense categories: Feed, Veterinary, Labor, Equipment, Utilities, Transport, Breeding
- Running balance always displayed
- Filter by type, category, date range

### Health Events
- Event types: Vaccination, Treatment, Deworming, Checkup, Surgery, Calving, Insemination
- Status tracking: Open → In Progress → Resolved
- Vet name, cost, and follow-up date
- Filter by status and event type

### Scheduled Tasks
- Priority levels: Low, Medium, High, Urgent
- Due date tracking with overdue warnings
- One-click mark as complete
- Filter by status tabs

### Employees
- Roles: Farm Manager, Milker, Vet Assistant, General Worker, Driver
- Monthly salary tracking
- Status: Active, On Leave, Terminated

### Reports
- **Milk PDF**: Date-range production report with totals
- **Milk CSV**: Export for Excel/Google Sheets
- **Finance PDF**: Transaction report with running balance
- **Finance CSV**: Full ledger export
- **Health PDF**: Health events summary
- All reports branded with farm name

## Mobile
- Fully responsive at 375px width
- Bottom navigation bar on mobile (Dashboard, Cows, Milk, Finance, Tasks)
- Touch-friendly buttons and forms

## MVP Checklist
- ✅ Farmer can register and login
- ✅ Add 5+ cows with profiles
- ✅ Record milk yields for 7+ days
- ✅ Correct daily/weekly totals displayed
- ✅ Record expense transactions
- ✅ Correct running balance shown
- ✅ Schedule 3+ health tasks
- ✅ Dashboard shows upcoming tasks
- ✅ Generate PDF reports
- ✅ All pages functional on 375px mobile

## Project Structure
```
milkflow_django/
├── manage.py
├── requirements.txt
├── README.md
├── milkflow/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── core/
    ├── models.py          # Farm, Cow, MilkRecord, HealthEvent, FinancialTransaction, ScheduledTask, Employee
    ├── views.py           # All views including PDF/CSV report generation
    ├── forms.py           # Django forms with validation
    ├── urls.py            # URL routing
    ├── apps.py
    ├── migrations/
    │   └── 0001_initial.py
    └── templates/core/
        ├── base.html      # Base with sidebar, mobile nav, delete modal
        ├── landing.html   # Public landing page
        ├── register.html
        ├── login.html
        ├── dashboard.html # Metrics + Chart.js trend
        ├── cow_list.html
        ├── cow_form.html
        ├── cow_detail.html
        ├── milk_list.html
        ├── milk_form.html # AM/PM auto-calculation
        ├── finance_list.html
        ├── finance_form.html # Dynamic category selector
        ├── health_list.html
        ├── health_form.html
        ├── task_list.html
        ├── task_form.html
        ├── employee_list.html
        ├── employee_form.html
        ├── reports.html
        └── farm_profile.html
```

## Color Theme
- Primary Green: `#2E7D32`
- Amber Secondary: `#F9A825`
- Background: `#F5F5F0`
- Typography: Sora (headings) + DM Sans (body)
