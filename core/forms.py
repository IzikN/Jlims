# core/forms.py

from django import forms
from .models import Client, Sample
from django.forms import modelformset_factory
from django import forms
from .models import Sample, TestParameter, TestAssignment, User, Batch, Worksheet, EquipmentLog, Worksheet, TestType, TestResult, Equipment
from django.forms import formset_factory
from .models import EquipmentLog

class WorksheetForm(forms.ModelForm):
    class Meta:
        model = Worksheet
        fields = ['title', 'test_parameter', 'assignments']
        widgets = {
            'assignments': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        super(WorksheetForm, self).__init__(*args, **kwargs)
        self.fields['assignments'].queryset = TestAssignment.objects.filter(status='Pending')



class BatchForm(forms.ModelForm):
    parameter = forms.ModelChoiceField(queryset=TestParameter.objects.all(), required=True)
    samples = forms.ModelMultipleChoiceField(
        queryset=Sample.objects.none(),  # 👈 Initially empty
        required=False
    )

    class Meta:
        model = Batch
        fields = ['parameter', 'samples']


class WorksheetEditForm(forms.ModelForm):
    assignments = forms.ModelMultipleChoiceField(
        queryset=TestAssignment.objects.filter(status='Pending'),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Worksheet
        fields = ['title', 'assignments']


class EquipmentLogForm(forms.ModelForm):
    class Meta:
        model = EquipmentLog
        fields = ['equipment', 'used_by', 'usage_date', 'start_time', 'end_time', 'status', 'note']
        widgets = {
            'usage_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['used_by'].initial = user
            self.fields['used_by'].widget.attrs['readonly'] = True

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})



class ResultSubmissionForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = ['value', 'unit']
        widgets = {
            'value': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter result'}),
            'unit': forms.TextInput(attrs={'placeholder': '% or mg/kg'}),
        }

        

class AssignTestForm(forms.Form):
    parameter = forms.ModelChoiceField(
        queryset=TestParameter.objects.all(),
        label="Test Parameter"
    )
    analyst = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Analyst'),
        label="Assign to Analyst"
    )
    deadline = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Deadline"
    )


AssignTestFormSet = formset_factory(AssignTestForm, extra=1)


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['client_id', 'name', 'organization', 'address', 'email', 'phone']

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['sample_id', 'nature_of_sample', 'weight', 'qc_flag', 'requested_parameters']
        widgets = {
            'qc_flag': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super(SampleForm, self).__init__(*args, **kwargs)

        grouped = []
        for test_type in TestType.objects.all():
            parameters = TestParameter.objects.filter(test_type=test_type)
            if parameters.exists():
                grouped.append((test_type.name, [(param.id, f"{param.name} (₦{param.price})") for param in parameters]))

        self.fields['requested_parameters'] = forms.MultipleChoiceField(
            choices=grouped,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'parameter-checkbox'}),
            label="Select Test Parameters",
            required=False
        )



SampleFormSet = modelformset_factory(
    Sample,
    form=SampleForm,
    extra=3,  # You can change to 10 or dynamic
    can_delete=False
)
