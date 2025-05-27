from django.shortcuts import render, get_object_or_404, redirect
from .models import Claim, Patient, Task, ActivityLog
from django import forms
from django.db.models import Count, Q
from django.db import transaction
import logging
from django.utils import timezone
from django.db import models
from django.contrib import messages

logger = logging.getLogger(__name__)

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'address_1', 'address_2', 'city', 'state', 
                 'zip_code', 'zip_plus_4', 'date_of_birth', 'gender']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

def home(request):
    """View for the home page"""
    # Get claim statistics
    total_claims = Claim.objects.count()
    submitted_claims = Claim.objects.filter(status='Submitted to Payer').count()
    approved_claims = Claim.objects.filter(status='Approved').count()
    denied_claims = Claim.objects.filter(status='Denied').count()
    
    # Get 5 most recent claims
    recent_claims = Claim.objects.select_related('patient').order_by('-service_date')[:5]
    
    context = {
        'total_claims': total_claims,
        'submitted_claims': submitted_claims,
        'approved_claims': approved_claims,
        'denied_claims': denied_claims,
        'recent_claims': recent_claims
    }
    
    return render(request, 'main/home.html', context)

def claims(request):
    """View for the claims page with search and filters."""
    claims = Claim.objects.select_related('patient').all()

    # Get filter params
    payer_name = request.GET.get('payer_name')
    payer_id = request.GET.get('payer_id')
    status = request.GET.get('status')
    search = request.GET.get('search')

    # Filtering
    if payer_name:
        claims = claims.filter(payer_name=payer_name)
    if payer_id:
        claims = claims.filter(payer_id=payer_id)
    if status:
        claims = claims.filter(status=status)
    if search:
        claims = claims.filter(
            models.Q(id__icontains=search) |
            models.Q(patient__external_patient_id__icontains=search) |
            models.Q(patient_name__icontains=search) |
            models.Q(payer_id__icontains=search) |
            models.Q(payer_name__icontains=search)
        )

    # Hardcoded dropdown options
    payer_names = [
        'New York Empire Blue Shield',
        'Oxford Health Plans',
        'New York Empire Medicare',
        'New York Medicaid',
        'Aenta',
        'Humana',
        'United Healthcare',
    ]
    payer_ids = [
        '00803', '06111', '11315', '13162', '13202', '13265', '87726'
    ]
    # Statuses for dropdown (with icon info for template)
    status_options = [
        {'value': 'Biller Received', 'label': 'Biller Received', 'icon': 'fa-inbox', 'color': '#a78bfa'},
        {'value': 'Coded', 'label': 'Coded', 'icon': 'fa-thumbs-up', 'color': '#6366f1'},
        {'value': 'Submitted to Payer', 'label': 'Submitted to Payer', 'icon': 'fa-paper-plane', 'color': '#3b82f6'},
        {'value': 'Missing Information', 'label': 'Missing Information', 'icon': 'fa-pen-square', 'color': '#fbbf24'},
        {'value': 'Not Billable', 'label': 'Not Billable', 'icon': 'fa-ban', 'color': '#64748b'},
        {'value': 'Waiting for Provider', 'label': 'Waiting for Provider', 'icon': 'fa-hourglass-half', 'color': '#fbbf24'},
        {'value': 'ERA Received', 'label': 'ERA Received', 'icon': 'fa-sync-alt', 'color': '#6366f1'},
        {'value': 'Rejected', 'label': 'Rejected', 'icon': 'fa-exclamation', 'color': '#fbbf24'},
        {'value': 'Denied', 'label': 'Denied', 'icon': 'fa-ban', 'color': '#f59e42'},
        {'value': 'Paid', 'label': 'Paid', 'icon': 'fa-dollar-sign', 'color': '#6366f1'},
        {'value': 'Paid Incorrectly', 'label': 'Paid Incorrectly', 'icon': 'fa-dollar-sign', 'color': '#fbbf24'},
        {'value': 'Finalized Paid', 'label': 'Finalized Paid', 'icon': 'fa-dollar-sign', 'color': '#22c55e'},
        {'value': 'Finalized Denied', 'label': 'Finalized Denied', 'icon': 'fa-ban', 'color': '#ef4444'},
        {'value': 'Held by Customer', 'label': 'Held by Customer', 'icon': 'fa-hand-paper', 'color': '#fbbf24'},
    ]

    context = {
        'claims': claims,
        'payer_names': payer_names,
        'payer_ids': payer_ids,
        'status_options': status_options,
        'selected_payer_name': payer_name or '',
        'selected_payer_id': payer_id or '',
        'selected_status': status or '',
        'search': search or '',
    }
    return render(request, 'main/claims.html', context)

@transaction.atomic
def claim_detail(request, claim_id):
    """View for the claim detail page"""
    logger.info(f"Processing claim_detail view for claim_id: {claim_id}")
    
    claim = get_object_or_404(Claim.objects.select_related('patient'), id=claim_id)
    logger.info(f"Found claim: {claim.id}, patient_name: {claim.patient_name}, patient: {claim.patient}")
    
    # Ensure claim has a linked patient
    if not claim.patient:
        logger.info(f"Claim {claim.id} has no linked patient, creating one")
        # Try to find existing patient by external_patient_id
        external_patient_id = f'DiaFref{claim.id}'
        try:
            patient = Patient.objects.get(external_patient_id=external_patient_id)
            logger.info(f"Found existing patient: {patient}")
        except Patient.DoesNotExist:
            # Create a new patient if one doesn't exist
            first_name = claim.patient_name.split()[0] if ' ' in claim.patient_name else claim.patient_name
            last_name = claim.patient_name.split()[1] if ' ' in claim.patient_name else ''
            patient = Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                address_1='119-15 27th Ave',
                city='Queens',
                state='NY',
                zip_code='11354',
                zip_plus_4='1011',
                date_of_birth='1941-02-04',
                gender='Female',
                external_patient_id=external_patient_id
            )
            logger.info(f"Created new patient: {patient}")
        
        # Link this claim to the patient
        claim.patient = patient
        claim.patient_name = patient.full_name
        claim.save()
        logger.info(f"Linked claim {claim.id} to patient {patient.id}")
    
    patient = claim.patient
    
    if request.method == 'POST':
        logger.info(f"Processing POST request for claim {claim.id}")
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            logger.info(f"Form is valid, saving patient {patient.id}")
            # Save the patient first
            patient = form.save(commit=False)
            patient.external_patient_id = patient.external_patient_id  # Preserve the external_patient_id
            patient.save()
            logger.info(f"Saved patient: {patient}")
            
            # Update all claims for this patient
            updated_claims = Claim.objects.filter(patient=patient).update(
                patient_name=patient.full_name
            )
            logger.info(f"Updated {updated_claims} claims for patient {patient.id}")
            
            # Force a refresh of the claim object
            claim.refresh_from_db()
            logger.info(f"Refreshed claim: {claim.id}, patient_name: {claim.patient_name}")
            
            return redirect('main:claim_detail', claim_id=claim_id)
        else:
            logger.error(f"Form validation failed: {form.errors}")
    else:
        form = PatientForm(instance=patient)
    
    context = {
        'claim': claim,
        'form': form,
        'patient': patient,
    }
    
    return render(request, 'main/claim_detail.html', context)

@transaction.atomic
def patient_detail(request, external_patient_id):
    logger.info(f"Processing patient_detail view for external_patient_id: {external_patient_id}")
    
    patient = get_object_or_404(Patient, external_patient_id=external_patient_id)
    logger.info(f"Found patient: {patient}")
    
    if request.method == 'POST':
        logger.info(f"Processing POST request for patient {patient.id}")
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            logger.info(f"Form is valid, saving patient {patient.id}")
            # Save the patient first
            patient = form.save(commit=False)
            patient.external_patient_id = external_patient_id  # Preserve the external_patient_id
            patient.save()
            logger.info(f"Saved patient: {patient}")
            
            # Update all claims for this patient
            updated_claims = Claim.objects.filter(patient=patient).update(
                patient_name=patient.full_name
            )
            logger.info(f"Updated {updated_claims} claims for patient {patient.id}")
            
            return redirect('main:patient_detail', external_patient_id=external_patient_id)
        else:
            logger.error(f"Form validation failed: {form.errors}")
    else:
        form = PatientForm(instance=patient)
    
    # Get all claims for this patient
    claims = Claim.objects.filter(patient=patient).order_by('-service_date')
    logger.info(f"Found {claims.count()} claims for patient {patient.id}")
    
    context = {
        'patient': patient,
        'form': form,
        'claims': claims,
    }
    return render(request, 'main/patient_detail.html', context)

def patients(request):
    logger.info("Processing patients view")
    # Get all patients with their claim counts, ordered by name
    patients = Patient.objects.annotate(
        claim_count=Count('claim')
    ).order_by('last_name', 'first_name')
    
    logger.info(f"Found {patients.count()} patients")
    return render(request, 'main/patients.html', {'patients': patients})

def tasks(request):
    # Filters from GET params
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    task_type = request.GET.get('task_type', '')
    assigned_to = request.GET.get('assigned_to', '')
    service_date = request.GET.get('service_date', '')
    search = request.GET.get('search', '')
    tasks = Task.objects.select_related('claim', 'patient').all()
    if status:
        tasks = tasks.filter(status=status)
    if category:
        tasks = tasks.filter(category=category)
    if task_type:
        tasks = tasks.filter(task_type=task_type)
    if assigned_to:
        tasks = tasks.filter(assigned_to=assigned_to)
    if service_date:
        tasks = tasks.filter(due_date=service_date)
    if search:
        tasks = tasks.filter(
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search) |
            Q(patient__external_patient_id__icontains=search) |
            Q(claim__payer_id__icontains=search)
        )
    # Prepare data for table
    task_rows = []
    for task in tasks:
        claim = task.claim
        patient = claim.patient if claim and claim.patient else task.patient
        task_rows.append({
            'id': task.id,
            'patient_name': patient.full_name if patient else '',
            'patient_external_id': patient.external_patient_id if patient else '',
            'payer_id': claim.payer_id if claim else '',
            'service_date': claim.service_date if claim else '',
            'last_updated': task.updated_at,
            'task_type': task.get_task_type_display(),
            'category': task.get_category_display(),
            'status': task.status,
            'created_by': 'Candid Health',
        })
    context = {
        'tasks': task_rows,
        'task_status_choices': Task.STATUS_CHOICES,
        'task_type_choices': Task.TYPE_CHOICES,
        'task_category_choices': Task.CATEGORY_CHOICES,
        'assigned_users': Task.objects.values_list('assigned_to', flat=True).distinct(),
    }
    return render(request, 'main/tasks.html', context)

@transaction.atomic
def task_detail(request, task_id):
    task = get_object_or_404(Task.objects.select_related('claim', 'patient'), id=task_id)
    claim = task.claim
    patient = claim.patient if claim and claim.patient else task.patient
    activity = task.activitylog_set.order_by('-timestamp')
    if request.method == 'POST':
        if 'close_task' in request.POST:
            if task.status != 'Completed':
                task.status = 'Completed'
                task.completed_at = timezone.now()
                task.save()
                ActivityLog.objects.create(task=task, message='Task closed by user.')
                messages.success(request, 'Task closed successfully.')
            return redirect('main:task_detail', task_id=task.id)
        elif 'add_message' in request.POST:
            message = request.POST.get('message', '').strip()
            if message:
                ActivityLog.objects.create(task=task, message=message)
                messages.success(request, 'Message added.')
            return redirect('main:task_detail', task_id=task.id)
    context = {
        'task': task,
        'claim': claim,
        'patient': patient,
        'activity': activity,
    }
    return render(request, 'main/task_detail.html', context)
