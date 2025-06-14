# core/models.py

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, date, time

class Client(models.Model):
    client_id = models.CharField(max_length=20, unique=True)  # e.g., JGLSP2505
    name = models.CharField(max_length=100)
    organization = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    date_received = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_id} - {self.name}"

class Sample(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="samples")
    sample_id = models.CharField(max_length=30)  # Manually entered
    nature_of_sample = models.CharField(max_length=100)
    weight = models.FloatField()
    status = models.CharField(max_length=30, default='Pending')  # e.g., Assigned, In Progress, Completed

    def __str__(self):
        return self.sample_id

class Batch(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    samples = models.ManyToManyField(Sample)

    def __str__(self):
        return self.name


class TestType(models.Model):
    name = models.CharField(max_length=100)  # Proximate, Aflatoxin, etc.

    def __str__(self):
        return self.name

class TestParameter(models.Model):
    test_type = models.ForeignKey(TestType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # Protein, Fat, etc.

    def __str__(self):
        return f"{self.test_type.name} - {self.name}"

class TestAssignment(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    parameter = models.ForeignKey(TestParameter, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'groups__name': 'Analyst'})
    deadline = models.DateField()
    result = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
    submitted_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"{self.sample.sample_id} - {self.parameter.name}"

class Worksheet(models.Model):
    title = models.CharField(max_length=150)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    test_parameter = models.ForeignKey(TestParameter, on_delete=models.CASCADE)
    assignments = models.ManyToManyField(TestAssignment)

    def __str__(self):
        return f"{self.title} ({self.test_parameter})"

class TestResult(models.Model):
    assignment = models.OneToOneField(TestAssignment, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=20)
    method = models.CharField(max_length=100)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.assignment} - {self.value}{self.unit}"

class Equipment(models.Model):
    name = models.CharField(max_length=100)
    model_number = models.CharField(max_length=50)
    serial_number = models.CharField(max_length=50)
    last_calibration = models.DateField()
    next_calibration = models.DateField()
    status = models.CharField(max_length=30)  # Working, Needs Maintenance

    def __str__(self):
        return self.name

class EquipmentLog(models.Model):
    STATUS_CHOICES = [
        ('Operational', 'Operational'),
        ('Faulty', 'Faulty'),
        ('Under Maintenance', 'Under Maintenance'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    usage_date = models.DateField(default=date.today)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Operational'
    )
    note = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            delta = datetime.combine(date.min, self.end_time) - datetime.combine(date.min, self.start_time)
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.equipment.name} used by {self.used_by} on {self.usage_date}"


class Reagent(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    expiry_date = models.DateField()
    storage = models.CharField(max_length=100)

    def __str__(self):
        return self.name


