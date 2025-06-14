# core/views.py

from django.shortcuts import render, redirect
from .forms import ClientForm, SampleFormSet
from django.forms import formset_factory
from django.contrib import messages
from .models import Sample
from .models import Client, Sample, TestAssignment, TestParameter, Equipment, EquipmentLog, Batch, Worksheet
from .forms import AssignTestForm  
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404

def home(request):
    return render(request, 'home.html')

@login_required
def create_worksheet(request):
    if request.method == 'POST':
        form = WorksheetForm(request.POST)
        if form.is_valid():
            worksheet = form.save(commit=False)
            worksheet.created_by = request.user
            worksheet.save()
            form.save_m2m()
            messages.success(request, "Worksheet created.")
            return redirect('manager_dashboard')
    else:
        form = WorksheetForm()
    return render(request, 'core/create_worksheet.html', {'form': form})


@login_required
def create_batch(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.created_by = request.user
            batch.save()
            form.save_m2m()
            messages.success(request, "Batch created successfully.")
            return redirect('manager_dashboard')
    else:
        form = BatchForm()
    return render(request, 'core/create_batch.html', {'form': form})

@login_required
def log_equipment_use(request):
    if request.method == 'POST':
        form = EquipmentLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.used_by = request.user
            log.save()
            messages.success(request, "Equipment log saved.")
            return redirect('analyst_dashboard')
    else:
        form = EquipmentLogForm()
    return render(request, 'core/equipment_log.html', {'form': form})


@login_required
def view_coa(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    samples = Sample.objects.filter(client=client)

    results = []
    for sample in samples:
        assignments = TestAssignment.objects.filter(sample=sample, status='Completed')
        results.append({
            'sample': sample,
            'assignments': assignments
        })

    return render(request, 'core/coa.html', {
        'client': client,
        'results': results
    })


def is_analyst(user):
    return user.groups.filter(name='Analyst').exists()

@login_required
@user_passes_test(is_analyst)
def analyst_dashboard(request):
    assignments = TestAssignment.objects.filter(
        assigned_to=request.user
    ).select_related('sample', 'parameter')

    total_samples = Sample.objects.count()
    completed_tests = TestAssignment.objects.filter(status='Completed').count()
    pending_tests = TestAssignment.objects.filter(status='Pending').count()
    equipment_status = Equipment.objects.values('status').annotate(count=Count('id'))

    context = {
        'assignments': assignments,
        'total_samples': total_samples,
        'completed_tests': completed_tests,
        'pending_tests': pending_tests,
        'equipment_status': equipment_status,
    }

    return render(request, 'core/analyst_dashboard.html', context)

@login_required
@user_passes_test(is_analyst)
def submit_result(request, assignment_id):
    assignment = get_object_or_404(TestAssignment, id=assignment_id, assigned_to=request.user)

    if request.method == 'POST':
        form = ResultSubmissionForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.status = 'Completed'
            assignment.submitted_at = timezone.now()
            assignment.save()
            messages.success(request, "Result submitted successfully.")
            return redirect('analyst_dashboard')
    else:
        form = ResultSubmissionForm(instance=assignment)

    return render(request, 'core/submit_result.html', {'form': form, 'assignment': assignment})


def is_manager(user):
    return user.groups.filter(name='Manager').exists()

@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    clients = Client.objects.prefetch_related('sample_set').order_by('-date_received')

    total_samples = Sample.objects.count()
    completed_tests = TestAssignment.objects.filter(status='Completed').count()
    pending_tests = TestAssignment.objects.filter(status='Pending').count()
    equipment_status = Equipment.objects.values('status').annotate(count=Count('id'))

    stats = get_dashboard_stats()

    context = {
        'clients': clients,
        'total_samples': total_samples,
        'completed_tests': completed_tests,
        'pending_tests': pending_tests,
        'equipment_status': equipment_status,
        **stats,
    }

    return render(request, 'core/manager_dashboard.html', context)

def is_cs(user):
    return user.groups.filter(name='Customer Service').exists()

@login_required
@user_passes_test(is_cs)
def cs_dashboard(request):
    clients = Client.objects.all().order_by('-date_received')
    return render(request, 'core/cs_dashboard.html', {'clients': clients})


@login_required
@user_passes_test(is_manager)
def assign_test(request, sample_id):
    sample = get_object_or_404(Sample, sample_id=sample_id)

    if request.method == 'POST':
        form = AssignTestForm(request.POST, sample=sample)
        if form.is_valid():
            form.save()
            messages.success(request, f"Test assigned for sample {sample.sample_id}")
            return redirect('manager_dashboard')
    else:
        form = AssignTestForm(sample=sample)

    return render(request, 'core/assign_test.html', {'form': form, 'sample': sample})


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.groups.filter(name='Manager').exists():
        return redirect('manager_dashboard')
    elif user.groups.filter(name='Customer Service').exists():
        return redirect('cs_dashboard')
    elif user.groups.filter(name='Analyst').exists():
        return redirect('analyst_dashboard')
    else:
        return redirect('admin:index')


@login_required
@user_passes_test(is_cs)
def create_test_request(request):
    if request.method == 'POST':
        client_form = ClientForm(request.POST)
        sample_formset = SampleFormSet(request.POST, queryset=Sample.objects.none())

        if client_form.is_valid() and sample_formset.is_valid():
            client = client_form.save()

            for form in sample_formset:
                sample = form.save(commit=False)
                sample.client = client
                sample.save()

            messages.success(request, "Test request successfully submitted.")
            return redirect('cs_dashboard')
    else:
        client_form = ClientForm()
        sample_formset = SampleFormSet(queryset=Sample.objects.none())

    return render(request, 'core/create_test_request.html', {
        'client_form': client_form,
        'sample_formset': sample_formset
    })
