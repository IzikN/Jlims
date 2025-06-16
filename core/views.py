from django.shortcuts import render, redirect
from .forms import ClientForm, SampleFormSet
from django.forms import formset_factory
from django.contrib import messages
from .models import Sample
from .models import Client, Sample, TestAssignment, TestParameter, Equipment, EquipmentLog, Batch, Worksheet
from .forms import AssignTestForm, ResultSubmissionForm, WorksheetForm, BatchForm, EquipmentLogForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils import timezone
from django.db.models import Count
from core.utils import save_audit 
from django.urls import reverse
from .forms import ResultSubmissionForm
import uuid
from .models import AuditTrail
from core.models import Invoice
from core.utils import calculate_total_price
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.http import JsonResponse
from .models import TestType, TestAssignment, TestResult
from django.forms import formset_factory
from .forms import AssignTestForm, AssignTestFormSet
from django.http import JsonResponse
from django.template.loader import render_to_string
from core.models import Client
from django.db.models import Count, Sum
from .models import Sample
from datetime import datetime, timedelta
from django.db.models.functions import TruncWeek, TruncMonth
from django.utils.dateparse import parse_date
import csv
from .models import Invoice 
from django.utils.timezone import now

def is_manager(user):
    return user.groups.filter(name='Manager').exists()

def is_analyst(user):
    return user.groups.filter(name='Analyst').exists()

def is_cs(user):
    return user.groups.filter(name='Customer Service').exists()

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

def home(request):
    client = Client.objects.first()  
    return render(request, 'home.html', {'client': client})



def worksheet_pdf(request, worksheet_id):
    worksheet = get_object_or_404(Worksheet, pk=worksheet_id)
    assignments = worksheet.test_assignments.select_related('sample', 'parameter')

    html_string = render_to_string('core/worksheet_pdf.html', {
        'worksheet': worksheet,
        'assignments': assignments
    })
    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="worksheet_{worksheet.id}.pdf"'
    return response


def calculate_total_price(client):
    samples = client.samples.all()
    total = 0
    for sample in samples:
        for assignment in sample.testassignment_set.all():
            total += assignment.parameter.price
    return total


def create_invoice_for_client(client):
    invoice_number = f"JGL-{uuid.uuid4().hex[:6].upper()}"
    total_amount = calculate_total_price(client)
    
    invoice = Invoice.objects.create(
        client=client,
        invoice_number=invoice_number,
        total_amount=total_amount,
        amount_paid=0
    )
    return invoice


def generate_invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    template = get_template('core/invoice_template.html')
    html = template.render({'invoice': invoice})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    pisa.CreatePDF(html, dest=response)
    save_audit(request.user, "Generated Invoice PDF", f"Invoice #{invoice.invoice_number}")  # ✅ audit
    return response

def generate_coa_pdf(request, client_id):
    # Get the client
    client = get_object_or_404(Client, client_id=client_id)

    # Get all test results related to the client
    results = TestResult.objects.filter(
        assignment__sample__client__client_id=client_id
    ).select_related('assignment__parameter', 'assignment__sample')

    # Load template
    template = get_template('core/coa_template.html')
    html = template.render({'client': client, 'results': results})

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="COA_{client_id}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating COA PDF", status=500)

    # Save audit
    save_audit(request.user, "Generated COA PDF", f"COA for Client ID {client_id}")
    
    return response

@login_required
def create_worksheet(request):
    if request.method == 'POST':
        form = WorksheetForm(request.POST)
        if form.is_valid():
            worksheet = form.save(commit=False)
            worksheet.created_by = request.user
            worksheet.title = f"{form.cleaned_data['test_parameter'].name} Worksheet {timezone.now().strftime('%Y%m%d%H%M%S')}"
            worksheet.save()
            form.save_m2m()

            # Mark each assignment as linked to a worksheet
            for assignment in form.cleaned_data['assignments']:
                assignment.worksheet = worksheet
                assignment.save()

            save_audit(request.user, "Created Worksheet", f"Worksheet ID #{worksheet.id}")
            messages.success(request, "Worksheet created successfully.")
            return redirect('worksheet_list')
    else:
        form = WorksheetForm()

    return render(request, 'core/create_worksheet.html', {'form': form})



@login_required
def filter_assignments(request):
    parameter_id = request.GET.get('parameter_id')
    assignments = TestAssignment.objects.filter(
        parameter_id=parameter_id, status='Pending'
    ).select_related('sample')

    data = [
        {"id": a.id, "label": f"{a.sample.sample_id} - {a.parameter.name}"}
        for a in assignments
    ]
    return JsonResponse({"assignments": data})


@login_required
@user_passes_test(is_manager)
def worksheet_list(request):
    worksheets = Worksheet.objects.all().order_by('-created_at')
    return render(request, 'core/worksheet_list.html', {'worksheets': worksheets})

@login_required
def worksheet_detail(request, pk):
    worksheet = get_object_or_404(Worksheet, pk=pk)
    assignments = worksheet.test_assignments.select_related(
        'sample__client',
        'parameter',
        'assigned_to'
    )

    results = TestResult.objects.filter(assignment__in=assignments)

    return render(request, 'core/worksheet_detail.html', {
        'worksheet': worksheet,
        'assignments': assignments,
        'results': results,
    })



@login_required
def worksheet_entry(request, worksheet_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id)

    # Optionally filter so analyst only sees their assignments
    assignments = worksheet.assignments.filter(assigned_to=request.user)

    if request.method == 'POST':
        for assignment in assignments:
            value = request.POST.get(f'value_{assignment.id}')
            unit = request.POST.get(f'unit_{assignment.id}')
            method = request.POST.get(f'method_{assignment.id}')

            if value and unit and method:
                result, created = TestResult.objects.get_or_create(
                    assignment=assignment,
                    defaults={'value': value, 'unit': unit, 'method': method}
                )

                if not created:
                    result.value = value
                    result.unit = unit
                    result.method = method
                    result.save()

                assignment.status = 'Completed'
                assignment.submitted_at = datetime.now()
                assignment.save()

        save_audit(request.user, "Submitted worksheet entries", f"Worksheet ID #{worksheet_id}")
        messages.success(request, "Worksheet entries submitted successfully.")
        return redirect('worksheet_list')

    return render(request, 'core/worksheet_entry.html', {
        'worksheet': worksheet,
        'assignments': assignments,
    })


@login_required
def create_batch(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.created_by = request.user
            batch.save()
            form.save_m2m()

            parameter = form.cleaned_data['parameter']
            selected_samples = form.cleaned_data['samples']

            # Link samples to the batch
            for sample in selected_samples:
                sample.batch = batch
                sample.save()

            # ✅ Automatically create TestAssignments for each sample
            created_assignments = []
            for sample in selected_samples:
                assignment = TestAssignment.objects.create(
                    sample=sample,
                    parameter=parameter,
                    status='Pending',
                    assigned_by=request.user,
                )
                created_assignments.append(assignment)

            # ✅ Create Worksheet for the batch
            worksheet = Worksheet.objects.create(
                title=f"{parameter.name} Worksheet for Batch #{batch.id}",
                test_parameter=parameter,
                created_by=request.user,
            )
            worksheet.assignments.set(created_assignments)

            # ✅ Set FK reference back in TestAssignments
            for assignment in created_assignments:
                assignment.worksheet = worksheet
                assignment.save()

            # ✅ Audit and success message
            save_audit(
                request.user,
                "Created Batch, Assigned Tests & Worksheet",
                f"Batch #{batch.id}, Worksheet #{worksheet.id}"
            )
            messages.success(request, "Batch, assignments, and worksheet created successfully.")
            return redirect('batch_list')
    else:
        form = BatchForm()

    return render(request, 'core/create_batch.html', {'form': form})

@login_required
def get_samples_for_parameter(request):
    parameter_id = request.GET.get('parameter_id')
    samples = Sample.objects.filter(
        requested_parameters__id=parameter_id,
        status='Pending',
        batch__isnull=True
    ).values('id', 'sample_id')
    return JsonResponse(list(samples), safe=False)


def view_client_results(request, token):
    client = get_object_or_404(Client, access_token=token)
    samples = client.samples.all().prefetch_related('testassignment_set__testresult')

    return render(request, 'core/client_results.html', {
        'client': client,
        'samples': samples,
    })

def client_token_entry(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        if Client.objects.filter(access_token=token).exists():
            return redirect('client_results', token=token)
        else:
            return render(request, 'core/token_entry.html', {'error': 'Invalid token.'})
    return render(request, 'core/token_entry.html')


@login_required
@user_passes_test(is_manager)
def edit_worksheet(request, worksheet_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id)
    assignments = worksheet.test_assignments.select_related('sample', 'parameter')

    analysts = User.objects.filter(groups__name='Analyst')  # Only analysts

    if request.method == 'POST':
        for assignment in assignments:
            analyst_id = request.POST.get(f'assignment_{assignment.id}')
            if analyst_id:
                assignment.assigned_to = User.objects.get(id=analyst_id)
                assignment.save()

        messages.success(request, "Analysts assigned successfully.")
        return redirect('worksheet_detail', worksheet_id=worksheet.id)

    return render(request, 'core/edit_worksheet.html', {
        'worksheet': worksheet,
        'assignments': assignments,
        'analysts': analysts,
    })


@login_required
@user_passes_test(is_manager)
def batch_list(request):
    batches = Batch.objects.all().order_by('-created_at')
    return render(request, 'core/batch_list.html', {'batches': batches})

@login_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    samples = batch.samples.all().prefetch_related('testassignment_set__testresult')

    total_assignments = 0
    completed_assignments = 0

    sample_data = []

    for sample in samples:
        assignments = sample.testassignment_set.all()
        total_assignments += assignments.count()
        completed_assignments += assignments.filter(status='Completed').count()

        sample_data.append({
            'sample': sample,
            'assignments': assignments,
        })

    completion_rate = 0
    if total_assignments > 0:
        completion_rate = int((completed_assignments / total_assignments) * 100)

    return render(request, 'core/batch_detail.html', {
        'batch': batch,
        'sample_data': sample_data,
        'completion_rate': completion_rate,
    })

@login_required
def log_equipment_use(request):
    if request.method == 'POST':
        form = EquipmentLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.used_by = request.user
            log.save()
            save_audit(request.user, "Logged Equipment Usage", f"Equipment: {log.equipment.name}")  # ✅ audit
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



@login_required
@user_passes_test(is_analyst)
def analyst_dashboard(request):
    user = request.user

    # Get assignments for this analyst
    assignments = TestAssignment.objects.filter(
        assigned_to=user
    ).select_related('sample', 'parameter', 'worksheet')

    # Extract related worksheets
    worksheet_ids = assignments.values_list('worksheet_id', flat=True).distinct()
    worksheets = Worksheet.objects.filter(id__in=worksheet_ids)

    # Create a mapping: assignment_id -> worksheet
    worksheet_map = {a.id: a.worksheet for a in assignments if a.worksheet}

    total_samples = Sample.objects.count()
    completed_tests = TestAssignment.objects.filter(status='Completed').count()
    pending_tests = TestAssignment.objects.filter(status='Pending').count()
    equipment_status = Equipment.objects.values('status').annotate(count=Count('id'))
    results = TestResult.objects.filter(assignment__in=assignments)
    result_map = {r.assignment_id: r for r in results}

    context = {
        'assignments': assignments,
        'worksheet_map': worksheet_map,
        'total_samples': total_samples,
        'completed_tests': completed_tests,
        'pending_tests': pending_tests,
        'equipment_status': equipment_status,
        'result_map': result_map,
    }

    return render(request, 'core/analyst_dashboard.html', context)



@login_required
@user_passes_test(is_analyst)
def submit_result(request, assignment_id):
    assignment = get_object_or_404(TestAssignment, id=assignment_id)

    if request.method == 'POST':
        form = ResultSubmissionForm(request.POST)
        if form.is_valid():
            result = form.save(commit=False)
            result.assignment = assignment
            result.save()

            assignment.status = 'Completed'
            assignment.save()

            save_audit(request.user, "Submitted result", f"{assignment.sample.sample_id} - {assignment.parameter.name}")
            messages.success(request, "Result submitted successfully.")
            return redirect('analyst_dashboard')
    else:
        form = ResultSubmissionForm()

    return render(request, 'core/submit_result.html', {'form': form, 'assignment': assignment})

@login_required
@user_passes_test(is_manager)
def submitted_results(request):
    assignments = TestAssignment.objects.filter(status='Completed').select_related('sample', 'parameter', 'assigned_to')
    return render(request, 'core/submitted_results.html', {
        'assignments': assignments
    })

@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    worksheets = Worksheet.objects.all().order_by('-created_at')[:5]
    clients = Client.objects.prefetch_related('samples').order_by('-date_received')

    total_samples = Sample.objects.count()
    completed_tests = TestAssignment.objects.filter(status='Completed').count()
    pending_tests = TestAssignment.objects.filter(status='Pending').count()
    equipment_status = Equipment.objects.values('status').annotate(count=Count('id'))
    #stats = get_dashboard_stats()

    audit_trails = AuditTrail.objects.order_by('-timestamp')[:20]  # 👈 recent logs

    context = {
        'clients': clients,
        'total_samples': total_samples,
        'completed_tests': completed_tests,
        'pending_tests': pending_tests,
        'equipment_status': equipment_status,
        'audit_trails': audit_trails,  # 👈 include in context
        'worksheets': worksheets,
    }

    return render(request, 'core/manager_dashboard.html', context)




@login_required
@user_passes_test(is_cs)
def cs_dashboard(request):
    clients = Client.objects.all().order_by('-date_received')
    search_query = request.GET.get('search')
    date_filter = request.GET.get('date')

    if search_query:
        clients = clients.filter(name__icontains=search_query)

    if date_filter:
        clients = clients.filter(date_received=date_filter)

    return render(request, 'core/cs_dashboard.html', {'clients': clients})

@login_required
@user_passes_test(is_manager)
def assign_test(request, sample_id):
    sample = get_object_or_404(Sample, sample_id=sample_id)

    if request.method == 'POST':
        formset = AssignTestFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:  # Avoid empty forms
                    TestAssignment.objects.create(
                        sample=sample,
                        parameter=TestParameter.objects.get(pk=form.cleaned_data['parameter']),
                        assigned_to=form.cleaned_data['analyst'],
                        deadline=form.cleaned_data['deadline'],
                        status='Pending'
                    )
            save_audit(request.user, "Assigned Test", f"Multiple tests assigned to sample {sample.sample_id}")
            messages.success(request, f"Tests successfully assigned for sample {sample.sample_id}")
            return redirect('manager_dashboard')
    else:
        formset = AssignTestFormSet()

    return render(request, 'core/assign_test.html', {
        'formset': formset,
        'sample': sample
    })




@login_required
@user_passes_test(is_cs)
def create_test_request(request):
    if request.method == 'POST':
        client_form = ClientForm(request.POST)

        if client_form.is_valid():
            client = client_form.save()
            posted_data = request.POST
            sample_index = 1
            samples_created = 0

            while f'sample_{sample_index}_sample_id' in posted_data:
                sample_id = posted_data.get(f'sample_{sample_index}_sample_id')
                nature = posted_data.get(f'sample_{sample_index}_nature_of_sample')
                weight = posted_data.get(f'sample_{sample_index}_weight')

                sample = Sample.objects.create(
                    client=client,
                    sample_id=sample_id,
                    nature_of_sample=nature,
                    weight=weight
                )

                param_keys = [key for key in posted_data if key.startswith(f'params_{sample_index}_param')]
                for key in param_keys:
                    param_ids = posted_data.getlist(key)
                    for pid in param_ids:
                        try:
                            param_obj = TestParameter.objects.get(pk=pid)
                            sample.requested_parameters.add(param_obj)
                        except TestParameter.DoesNotExist:
                            continue

                samples_created += 1
                sample_index += 1

            # ✅ Invoice created using helper
            invoice = create_invoice_for_client(client)

            # ✅ Save and email PDF
            generate_invoice_pdf_and_email(invoice.id, request.user)

            # ✅ Audit
            save_audit(request.user, "Created Test Request", f"Client ID {client.client_id} with {samples_created} sample(s)")

            # ✅ Message and redirect
            messages.success(
                request,
                f"Test request submitted! Client ID: {client.client_id}, Token: {client.access_token}. "
                f"<a href='{reverse('generate_invoice_pdf', args=[invoice.id])}' target='_blank' class='text-blue-600 underline'>Download Invoice PDF</a>"
            )
            return redirect('cs_dashboard')

        else:
            messages.error(request, "Client information is invalid.")
    else:
        client_form = ClientForm()

    return render(request, 'core/create_test_request.html', {
        'client_form': client_form
    })


@login_required
def client_submission_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    samples = client.samples.prefetch_related('requested_parameters')

    return render(request, 'core/client_submission_detail.html', {
        'client': client,
        'samples': samples,
    })

@login_required
def api_get_test_parameters(request):
    data = []
    for t in TestType.objects.prefetch_related('testparameter_set'):
        data.append({
            'test_type': t.name,
            'parameters': [
                {'id': p.id, 'name': p.name, 'price': float(p.price)}
                for p in t.testparameter_set.all()
            ]
        })
    return JsonResponse(data, safe=False)




@login_required
def load_samples(request):
    parameter_id = request.GET.get('parameter')
    samples = Sample.objects.filter(
        testassignment__parameter_id=parameter_id,
        status='Pending'
    ).distinct()
    context = {'samples': samples}
    html = render_to_string('core/sample_checkbox_list.html', context)
    return JsonResponse(html, safe=False)



def statistics_dashboard(request):
    today = datetime.today()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        start = today - timedelta(days=30)
        end = today

    # Get samples within date range based on Client's date_received field
    samples = Sample.objects.filter(client__date_received__range=[start, end])

    # 1. Total number of samples
    total_samples = samples.count()

    # 2. Total amount: sum of all requested parameters' prices for these samples
    total_amount = (
        TestParameter.objects
        .filter(sample__in=samples)
        .aggregate(total=Sum('price'))['total']
    ) or 0

    # 3. Top 5 clients by total test charges
    top_clients = (
        samples
        .values('client__name')
        .annotate(total=Sum('requested_parameters__price'))
        .order_by('-total')[:5]
    )

    # 4. Weekly revenue based on client's date_received
    weekly_revenue = (
        samples
        .annotate(week=TruncWeek('client__date_received'))
        .values('week')
        .annotate(total=Sum('requested_parameters__price'))
        .order_by('-week')
    )
    highest_week = weekly_revenue[0] if weekly_revenue else None

    # 5. Monthly revenue based on client's date_received
    monthly_revenue = (
        samples
        .annotate(month=TruncMonth('client__date_received'))
        .values('month')
        .annotate(total=Sum('requested_parameters__price'))
        .order_by('-month')
    )
    highest_month = monthly_revenue[0] if monthly_revenue else None

    context = {
        'total_samples': total_samples,
        'total_amount': total_amount,
        'top_clients': top_clients,
        'highest_week': highest_week,
        'highest_month': highest_month,
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
    }

    return render(request, 'core/statistics_dashboard.html', context)

def download_statistics_csv(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start = parse_date(start_date)
        end = parse_date(end_date)
    else:
        end = datetime.today().date()
        start = end - timedelta(days=30)

    samples = Sample.objects.filter(client__date_received__range=[start, end])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="jaagee_statistics_{start}_{end}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Client Name', 'Sample ID', 'Date Received', 'Test Parameter', 'Price'])

    for sample in samples:
        for param in sample.requested_parameters.all():
            writer.writerow([
                sample.client.name,
                sample.sample_id,
                sample.client.date_received.strftime('%Y-%m-%d'),
                param.name,
                param.price
            ])

    # Summary row (optional)
    writer.writerow([])
    writer.writerow(['Total Samples', samples.count()])
    total = TestParameter.objects.filter(sample__in=samples).aggregate(total=Sum('price'))['total'] or 0
    writer.writerow(['Total Revenue', f'₦{total}'])

    return response