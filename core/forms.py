from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Farm, Cow, MilkRecord, HealthEvent, FinancialTransaction, ScheduledTask, Employee
from datetime import date


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    full_name = forms.CharField(max_length=150, required=False,
                                 widget=forms.TextInput(attrs={'placeholder': 'John Doe'}))
    farm_name = forms.CharField(max_length=200, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Sunrise Dairy Farm'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'farm_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        name_parts = self.cleaned_data.get('full_name', '').split(' ', 1)
        user.first_name = name_parts[0] if name_parts else ''
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        if commit:
            user.save()
            Farm.objects.create(user=user, name=self.cleaned_data['farm_name'])
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['name', 'location', 'phone', 'email', 'registration_number', 'established_date', 'notes']
        widgets = {
            'established_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class CowForm(forms.ModelForm):
    class Meta:
        model = Cow
        fields = ['tag_number', 'name', 'breed', 'date_of_birth', 'date_acquired',
                  'status', 'weight_kg', 'notes']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_acquired': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean_tag_number(self):
        tag = self.cleaned_data.get('tag_number', '').strip()
        if not tag:
            raise forms.ValidationError("Tag number is required.")
        return tag.upper()


class MilkRecordForm(forms.ModelForm):
    class Meta:
        model = MilkRecord
        fields = ['cow', 'record_date', 'am_yield', 'pm_yield', 'notes']
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'am_yield': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'placeholder': '0.0'}),
            'pm_yield': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'placeholder': '0.0'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['cow'].queryset = Cow.objects.filter(user=user, status__in=['active', 'pregnant'])
            self.fields['cow'].empty_label = '— Herd / General —'
        self.fields['record_date'].initial = date.today()

    def clean(self):
        cleaned = super().clean()
        am = cleaned.get('am_yield', 0) or 0
        pm = cleaned.get('pm_yield', 0) or 0
        if am < 0 or pm < 0:
            raise forms.ValidationError("Yield values cannot be negative.")
        if am == 0 and pm == 0:
            raise forms.ValidationError("At least one yield (AM or PM) must be greater than 0.")
        return cleaned


class HealthEventForm(forms.ModelForm):
    class Meta:
        model = HealthEvent
        fields = ['cow', 'event_date', 'event_type', 'description', 'treatment',
                  'vet_name', 'cost', 'status', 'follow_up_date']
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['cow'].queryset = Cow.objects.filter(user=user)
            self.fields['cow'].empty_label = '— Entire Herd —'
        self.fields['event_date'].initial = date.today()


class FinancialTransactionForm(forms.ModelForm):
    INCOME_CATEGORIES = FinancialTransaction.INCOME_CATEGORIES
    EXPENSE_CATEGORIES = FinancialTransaction.EXPENSE_CATEGORIES

    class Meta:
        model = FinancialTransaction
        fields = ['transaction_date', 'transaction_type', 'category', 'description', 'amount', 'reference']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'description': forms.TextInput(attrs={'placeholder': 'Brief description'}),
            'reference': forms.TextInput(attrs={'placeholder': 'Receipt/Invoice #'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_date'].initial = date.today()
        # Categories will be filtered by JS based on transaction_type

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class ScheduledTaskForm(forms.ModelForm):
    class Meta:
        model = ScheduledTask
        fields = ['title', 'task_type', 'cow', 'due_date', 'priority', 'description']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['cow'].queryset = Cow.objects.filter(user=user)
            self.fields['cow'].empty_label = '— All / General —'

    def clean_due_date(self):
        due = self.cleaned_data.get('due_date')
        return due  # Allow past dates for recording purposes


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['full_name', 'role', 'phone', 'email', 'national_id',
                  'hire_date', 'monthly_salary', 'status', 'notes']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'monthly_salary': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class DateRangeForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
