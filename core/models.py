from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class Farm(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farm')
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    established_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def active_cow_count(self):
        return self.user.cows.filter(status='active').count()


class Cow(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('dry', 'Dry'),
        ('pregnant', 'Pregnant'),
        ('sold', 'Sold'),
        ('deceased', 'Deceased'),
    ]
    BREED_CHOICES = [
        ('Friesian', 'Friesian'),
        ('Ayrshire', 'Ayrshire'),
        ('Jersey', 'Jersey'),
        ('Guernsey', 'Guernsey'),
        ('Holstein', 'Holstein'),
        ('Brown Swiss', 'Brown Swiss'),
        ('Crossbreed', 'Crossbreed'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cows')
    tag_number = models.CharField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    breed = models.CharField(max_length=50, choices=BREED_CHOICES, default='Friesian')
    date_of_birth = models.DateField(null=True, blank=True)
    date_acquired = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['tag_number']
        unique_together = ['user', 'tag_number']

    def __str__(self):
        return f"{self.tag_number} — {self.name or 'Unnamed'}"

    @property
    def age_display(self):
        if not self.date_of_birth:
            return 'Unknown'
        today = date.today()
        delta = today - self.date_of_birth
        years = delta.days // 365
        months = (delta.days % 365) // 30
        if years > 0:
            return f"{years}y {months}m"
        return f"{months} months"

    @property
    def total_milk_today(self):
        today = date.today()
        qs = self.milk_records.filter(record_date=today)
        return sum(r.total_yield for r in qs)


class MilkRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='milk_records')
    cow = models.ForeignKey(Cow, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='milk_records')
    record_date = models.DateField(default=date.today)
    am_yield = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                    verbose_name='AM Yield (L)')
    pm_yield = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                    verbose_name='PM Yield (L)')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-record_date', '-created_at']

    def __str__(self):
        return f"{self.record_date} — {self.cow or 'General'} — {self.total_yield}L"

    @property
    def total_yield(self):
        return (self.am_yield or 0) + (self.pm_yield or 0)


class HealthEvent(models.Model):
    EVENT_TYPES = [
        ('vaccination', 'Vaccination'),
        ('treatment', 'Treatment'),
        ('deworming', 'Deworming'),
        ('checkup', 'Routine Checkup'),
        ('surgery', 'Surgery'),
        ('injury', 'Injury'),
        ('disease', 'Disease'),
        ('calving', 'Calving'),
        ('insemination', 'Insemination'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_events')
    cow = models.ForeignKey(Cow, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='health_events')
    event_date = models.DateField(default=date.today)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    description = models.TextField()
    treatment = models.TextField(blank=True)
    vet_name = models.CharField(max_length=100, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.event_date} — {self.get_event_type_display()} — {self.cow or 'Herd'}"


class FinancialTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    INCOME_CATEGORIES = [
        ('milk_sales', 'Milk Sales'),
        ('animal_sales', 'Animal Sales'),
        ('manure_sales', 'Manure Sales'),
        ('grants', 'Grants / Subsidies'),
        ('other_income', 'Other Income'),
    ]
    EXPENSE_CATEGORIES = [
        ('feed', 'Feed & Fodder'),
        ('veterinary', 'Veterinary'),
        ('labor', 'Labor / Wages'),
        ('equipment', 'Equipment'),
        ('utilities', 'Utilities'),
        ('transport', 'Transport'),
        ('breeding', 'Breeding / AI'),
        ('other_expense', 'Other Expense'),
    ]
    ALL_CATEGORIES = INCOME_CATEGORIES + EXPENSE_CATEGORIES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField(default=date.today)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=30)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.transaction_date} — {self.get_transaction_type_display()} — KES {self.amount}"

    def get_category_display_name(self):
        cats = dict(self.ALL_CATEGORIES)
        return cats.get(self.category, self.category.replace('_', ' ').title())


class ScheduledTask(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    TASK_TYPES = [
        ('vaccination', 'Vaccination'),
        ('deworming', 'Deworming'),
        ('checkup', 'Vet Checkup'),
        ('feeding', 'Special Feeding'),
        ('breeding', 'Breeding / AI'),
        ('maintenance', 'Farm Maintenance'),
        ('purchase', 'Purchase'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    cow = models.ForeignKey(Cow, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-priority']

    def __str__(self):
        return f"{self.due_date} — {self.title}"

    @property
    def is_overdue(self):
        return self.status == 'pending' and self.due_date < date.today()

    @property
    def days_until_due(self):
        delta = self.due_date - date.today()
        return delta.days


class Employee(models.Model):
    ROLE_CHOICES = [
        ('farm_manager', 'Farm Manager'),
        ('milker', 'Milker'),
        ('veterinary_assistant', 'Veterinary Assistant'),
        ('general_worker', 'General Worker'),
        ('driver', 'Driver'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employees')
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='general_worker')
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    national_id = models.CharField(max_length=30, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} — {self.get_role_display()}"
