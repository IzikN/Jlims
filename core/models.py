from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, date, time
import uuid

class Client(models.Model):
    client_id = models.CharField(max_length=20, unique=True)
    access_token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
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
    requested_parameters = models.ManyToManyField('TestParameter', blank=True)
    batch = models.ForeignKey('Batch', on_delete=models.SET_NULL, null=True, blank=True, related_name='sample_set')
    sample_id = models.CharField(max_length=30)
    nature_of_sample = models.CharField(max_length=100)
    weight = models.FloatField()
    status = models.CharField(max_length=30, default='Pending')  # Pending, In Progress, Completed
    qc_flag = models.CharField(
        max_length=20,
        choices=[
            ('', 'None'),
            ('Control', 'Control'),
            ('Duplicate', 'Duplicate'),
        ],
        default='',
        blank=True
    )

    def __str__(self):
        return self.sample_id
    


class Batch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    samples = models.ManyToManyField('Sample', related_name='batches')
    parameter = models.ForeignKey('TestParameter', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class TestType(models.Model):
    name = models.CharField(max_length=100)  # Proximate, Aflatoxin, etc.

    def __str__(self):
        return self.name


class TestParameter(models.Model):
    test_type = models.ForeignKey('TestType', on_delete=models.SET_NULL, null=True, blank=True) 
    name = models.CharField(max_length=100)  # Protein, Fat, Ash, etc.
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1000)

    def __str__(self):
        return f"{self.name} - ₦{self.price}"

class ReferenceRange(models.Model):
    parameter = models.OneToOneField(TestParameter, on_delete=models.CASCADE)
    min_value = models.DecimalField(max_digits=6, decimal_places=2)
    max_value = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=20, default='%')  # e.g., %, mg/kg

    def __str__(self):
        return f"{self.parameter.name} Range ({self.min_value}–{self.max_value} {self.unit})"


class TestAssignment(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    parameter = models.ForeignKey(TestParameter, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')])
    worksheet = models.ForeignKey('Worksheet', null=True, blank=True, on_delete=models.SET_NULL, related_name='test_assignments')
    def __str__(self):
        return f"{self.sample.sample_id} - {self.parameter.name}"


class Worksheet(models.Model):
    title = models.CharField(max_length=100)
    test_parameter = models.ForeignKey('TestParameter', on_delete=models.CASCADE)
    assignments = models.ManyToManyField('TestAssignment', related_name='worksheets')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TestResult(models.Model):
    assignment = models.OneToOneField(TestAssignment, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=20, default='%')
    submitted_at = models.DateTimeField(auto_now_add=True)

    @property
    def in_range(self):
        try:
            reference = ReferenceRange.objects.get(parameter=self.assignment.parameter)
            return reference.min_value <= self.value <= reference.max_value
        except ReferenceRange.DoesNotExist:
            return None  # No range defined

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Operational')
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


class Invoice(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_issued = models.DateTimeField(auto_now_add=True)
    invoice_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.invoice_number


class AuditTrail(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"
