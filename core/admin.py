from django.contrib import admin
from .models import *

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'name', 'phone', 'date_received']
    search_fields = ['client_id', 'name']

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ['sample_id', 'client', 'status', 'weight']
    search_fields = ['sample_id', 'client__client_id']

@admin.register(TestType)
class TestTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(TestParameter)
class TestParameterAdmin(admin.ModelAdmin):
    list_display = ['name', 'test_type']

@admin.register(TestAssignment)
class TestAssignmentAdmin(admin.ModelAdmin):
    list_display = ['sample', 'parameter', 'assigned_to', 'status']
    list_filter = ['assigned_to', 'status']

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'value', 'unit', 'submitted_at']

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_number', 'next_calibration', 'status']

from django.contrib import admin
from .models import EquipmentLog

@admin.register(EquipmentLog)
class EquipmentLogAdmin(admin.ModelAdmin):
    list_display = [
        'equipment',
        'used_by',
        'usage_date',
        'start_time',
        'end_time',
        'duration_minutes',
        'status',
    ]

@admin.register(Reagent)
class ReagentAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'unit', 'expiry_date']
