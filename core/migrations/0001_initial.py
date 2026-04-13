from django.db import migrations, models
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Farm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('location', models.CharField(blank=True, max_length=300)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('registration_number', models.CharField(blank=True, max_length=100)),
                ('established_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='farm', to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='Cow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_number', models.CharField(max_length=50)),
                ('name', models.CharField(blank=True, max_length=100)),
                ('breed', models.CharField(choices=[('Friesian', 'Friesian'), ('Ayrshire', 'Ayrshire'), ('Jersey', 'Jersey'), ('Guernsey', 'Guernsey'), ('Holstein', 'Holstein'), ('Brown Swiss', 'Brown Swiss'), ('Crossbreed', 'Crossbreed'), ('Other', 'Other')], default='Friesian', max_length=50)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('date_acquired', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('dry', 'Dry'), ('pregnant', 'Pregnant'), ('sold', 'Sold'), ('deceased', 'Deceased')], default='active', max_length=20)),
                ('weight_kg', models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cows', to='auth.user')),
            ],
            options={'ordering': ['tag_number']},
        ),
        migrations.AddConstraint(
            model_name='cow',
            constraint=models.UniqueConstraint(fields=['user', 'tag_number'], name='unique_cow_tag_per_user'),
        ),
        migrations.CreateModel(
            name='MilkRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_date', models.DateField(default=datetime.date.today)),
                ('am_yield', models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='AM Yield (L)')),
                ('pm_yield', models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='PM Yield (L)')),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cow', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='milk_records', to='core.cow')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milk_records', to='auth.user')),
            ],
            options={'ordering': ['-record_date', '-created_at']},
        ),
        migrations.CreateModel(
            name='HealthEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_date', models.DateField(default=datetime.date.today)),
                ('event_type', models.CharField(choices=[('vaccination', 'Vaccination'), ('treatment', 'Treatment'), ('deworming', 'Deworming'), ('checkup', 'Routine Checkup'), ('surgery', 'Surgery'), ('injury', 'Injury'), ('disease', 'Disease'), ('calving', 'Calving'), ('insemination', 'Insemination'), ('other', 'Other')], max_length=30)),
                ('description', models.TextField()),
                ('treatment', models.TextField(blank=True)),
                ('vet_name', models.CharField(blank=True, max_length=100)),
                ('cost', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')], default='open', max_length=20)),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cow', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='health_events', to='core.cow')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_events', to='auth.user')),
            ],
            options={'ordering': ['-event_date']},
        ),
        migrations.CreateModel(
            name='FinancialTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_date', models.DateField(default=datetime.date.today)),
                ('transaction_type', models.CharField(choices=[('income', 'Income'), ('expense', 'Expense')], max_length=10)),
                ('category', models.CharField(max_length=30)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('reference', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='auth.user')),
            ],
            options={'ordering': ['-transaction_date', '-created_at']},
        ),
        migrations.CreateModel(
            name='ScheduledTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('due_date', models.DateField()),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=15)),
                ('task_type', models.CharField(choices=[('vaccination', 'Vaccination'), ('deworming', 'Deworming'), ('checkup', 'Vet Checkup'), ('feeding', 'Special Feeding'), ('breeding', 'Breeding / AI'), ('maintenance', 'Farm Maintenance'), ('purchase', 'Purchase'), ('other', 'Other')], default='other', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cow', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='core.cow')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='auth.user')),
            ],
            options={'ordering': ['due_date', '-priority']},
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150)),
                ('role', models.CharField(choices=[('farm_manager', 'Farm Manager'), ('milker', 'Milker'), ('veterinary_assistant', 'Veterinary Assistant'), ('general_worker', 'General Worker'), ('driver', 'Driver'), ('other', 'Other')], default='general_worker', max_length=30)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('national_id', models.CharField(blank=True, max_length=30)),
                ('hire_date', models.DateField(blank=True, null=True)),
                ('monthly_salary', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('active', 'Active'), ('on_leave', 'On Leave'), ('terminated', 'Terminated')], default='active', max_length=15)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='auth.user')),
            ],
            options={'ordering': ['full_name']},
        ),
    ]
