from django.contrib import admin
from .models import *

from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    readonly_fields = ('client_id', 'access_token')
    list_display = ('client_id', 'name', 'organization', 'access_token', 'date_received')


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ['sample_id', 'client', 'status', 'weight', 'qc_flag']
    list_filter = ['qc_flag', 'status']
    search_fields = ['sample_id', 'client__client_id']

@admin.register(ReferenceRange)
class ReferenceRangeAdmin(admin.ModelAdmin):
    list_display = ['parameter', 'min_value', 'max_value', 'unit']


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
    list_display = ['assignment', 'value', 'unit', 'submitted_at', 'is_in_range']
    readonly_fields = ['is_in_range']

    def is_in_range(self, obj):
        result = obj.in_range
        if result is True:
            return "✅ In Range"
        elif result is False:
            return "⚠️ Out of Range"
        return "❓ No Range"
    is_in_range.short_description = "Range Status"

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_number', 'next_calibration', 'status']

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

class SampleInline(admin.TabularInline):
    model = Sample
    extra = 0
    fields = ['sample_id', 'nature_of_sample', 'weight', 'qc_flag']
    readonly_fields = ['sample_id', 'nature_of_sample', 'weight', 'qc_flag']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    inlines = [SampleInline]  # ✅ shows related samples inline


# admin.py
class WorksheetAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_parameter', 'created_by', 'created_at')  # remove 'is_closed'
    list_filter = ('test_parameter',)  # remove 'is_closed'
