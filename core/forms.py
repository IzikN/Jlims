# core/forms.py

from django import forms
from .models import Client, Sample
from django.forms import modelformset_factory
from django import forms
from .models import Sample, TestParameter, TestAssignment, User, Batch, Worksheet, EquipmentLog

class WorksheetForm(forms.ModelForm):
    class Meta:
        model = Worksheet
        fields = ['title', 'test_parameter', 'assignments']
        widgets = {'assignments': forms.CheckboxSelectMultiple}

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'samples']
        widgets = {'samples': forms.CheckboxSelectMultiple}

class EquipmentLogForm(forms.ModelForm):
    class Meta:
        model = EquipmentLog
        fields = ['equipment', 'start_time', 'end_time', 'status', 'note']

class ResultSubmissionForm(forms.ModelForm):
    class Meta:
        model = TestAssignment
        fields = ['result']

    def __init__(self, *args, **kwargs):
        super(ResultSubmissionForm, self).__init__(*args, **kwargs)
        self.fields['result'].label = "Enter Result"

class AssignTestForm(forms.Form):
    parameter = forms.ModelChoiceField(queryset=TestParameter.objects.all())
    analyst = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='Analyst'))

    def __init__(self, *args, **kwargs):
        self.sample = kwargs.pop('sample')
        super().__init__(*args, **kwargs)

    def save(self):
        assignment = TestAssignment.objects.create(
            sample=self.sample,
            parameter=self.cleaned_data['parameter'],
            assigned_to=self.cleaned_data['analyst'],
            status='Pending'
        )
        return assignment

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['client_id', 'name', 'organization', 'address', 'email', 'phone']

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['sample_id', 'nature_of_sample', 'weight']


SampleFormSet = modelformset_factory(
    Sample,
    form=SampleForm,
    extra=3,  # You can change to 10 or dynamic
    can_delete=False
)
