from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from .models import Claim, Task, Patient
from django import forms
from django.db.models import Count
from django.core.cache import cache
from datetime import datetime, timedelta
from django.db.models import Q
from django.core.paginator import Paginator



class PatientForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    address_1 = forms.CharField(max_length=255, required=True)
    address_2 = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=2, required=True)
    zip_code = forms.CharField(max_length=10, required=True)
    zip_plus_4 = forms.CharField(max_length=4, required=False)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], required=True)
    external_patient_id = forms.CharField(max_length=100, required=False)
    external_encounter_id = forms.CharField(max_length=100, required=False)
    patient_control_number = forms.CharField(max_length=100, required=False)

def home(request):
    """View for the home page"""
    # Get claim statistics
    total_claims = Claim.objects.count()
    submitted_claims = Claim.objects.filter(status='Submitted to Payer').count()
    approved_claims = Claim.objects.filter(status='Approved').count()
    denied_claims = Claim.objects.filter(status='Denied').count()
    
    # Get 5 most recent claims
    recent_claims = Claim.objects.all().order_by('-service_date')[:5]
    
    context = {
        'total_claims': total_claims,
        'submitted_claims': submitted_claims,
        'approved_claims': approved_claims,
        'denied_claims': denied_claims,
        'recent_claims': recent_claims
    }
    
    return render(request, 'main/home.html', context)

def claims(request):
    """View for the claims page"""
    claims = Claim.objects.all()
    return render(request, 'main/claims.html', {'claims': claims})

def claim_detail(request, claim_id):
    """View for the claim detail page"""
    claim = get_object_or_404(Claim, id=claim_id)
    
    # Default values - in a real app, these would come from a Patient model
    # This is just for demonstration
    initial_data = {
        'first_name': claim.patient_name.split()[0] if ' ' in claim.patient_name else claim.patient_name,
        'last_name': claim.patient_name.split()[1] if ' ' in claim.patient_name else '',
        'address_1': '119-15 27th Ave',
        'city': 'Queens',
        'state': 'NY',
        'zip_code': '11354',
        'zip_plus_4': '1011',
        'date_of_birth': '1941-02-04',  # Demo data
        'gender': 'Female',
        'external_patient_id': f'DiaFref{claim.id}',
        'external_encounter_id': f'671827355babc9781159d1bf',
        'patient_control_number': f'QF2G...4V1Z',
    }
    
    form = PatientForm(initial=initial_data)
    
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            # Process form data
            # In a real app, you would update the patient record
            # For demo, we'll just redirect back
            return redirect('main:claim_detail', claim_id=claim_id)
    
    context = {
        'claim': claim,
        'form': form,
    }
    
    return render(request, 'main/claim_detail.html', context)

def patient_detail(request, external_patient_id):
    # For demo, find the first claim with this external_patient_id
    claim = Claim.objects.first()  # Replace with actual lookup logic if you have a Patient model
    form = PatientForm(initial={
        'first_name': claim.patient_name.split()[0] if ' ' in claim.patient_name else claim.patient_name,
        'last_name': claim.patient_name.split()[1] if ' ' in claim.patient_name else '',
        'address_1': '9 Hilaire Dr',
        'city': 'Huntington',
        'state': 'NY',
        'zip_code': '11743',
        'zip_plus_4': '3768',
        'date_of_birth': '1947-05-11',
        'gender': 'Male',
        'external_patient_id': external_patient_id,
    })
    context = {
        'claim': claim,
        'form': form,
    }
    return render(request, 'main/patient_detail.html', context)

def patients(request):
    # For demo, get unique patient names from claims
    patient_names = Claim.objects.values_list('patient_name', flat=True).distinct()
    patients = [{'name': name, 'external_patient_id': f'SchA...{str(i).zfill(4)}'} for i, name in enumerate(patient_names, 1)]
    return render(request, 'main/patients.html', {'patients': patients})


def get_tasks():
    tasks = cache.get('tasks')
    if not tasks:
        # Initialize with some sample tasks if none exist
        tasks = [
            {
                'id': 1,
                'title': 'Review denied claim',
                'status': 'Open',
                'category': 'Billing',
                'type': 'Denial Management',
                'assigned_to': 'John Doe',
                'due_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                'claim_id': 1,  # Reference to existing claim
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        cache.set('tasks', tasks)
    return tasks

def save_tasks(tasks):
    cache.set('tasks', tasks)

def tasks(request):
    # Get filter parameters from request
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    task_type_filter = request.GET.get('type')
    assigned_filter = request.GET.get('assigned')
    service_date_filter = request.GET.get('service_date')
    search_query = request.GET.get('search')

    # Start with all claims that need attention (status != Approved)
    claims = Claim.objects.exclude(status='Approved')

    # Apply filters
    if status_filter:
        claims = claims.filter(status=status_filter)
    if service_date_filter:
        claims = claims.filter(service_date=service_date_filter)
    if search_query:
        claims = claims.filter(
            Q(patient_name__icontains=search_query) |
            Q(payer_name__icontains=search_query) |
            Q(payer_id__icontains=search_query)
        )

    # Convert claims to task-like structure
    tasks = []
    for claim in claims:
        # Determine task type based on claim status
        if claim.status == 'Denied':
            task_type = 'Denial Management'
            category = 'Billing'
            completion_status = 'Open'  # Default status for denied claims
        elif claim.status == 'Pending':
            task_type = 'Claim Review'
            category = 'Coding'
            completion_status = 'Open'  # Default status for pending claims
        else:  # Submitted to Payer
            task_type = 'Payment Follow Up'
            category = 'Billing'
            completion_status = 'In Progress'  # Default status for submitted claims
        
        tasks.append({
            'id': claim.id,
            'claim': claim,
            'status': completion_status,
            'category': category,
            'task_type': task_type,
            'assigned_to': '',  # Can be set based on your logic
            'due_date': claim.service_date + timedelta(days=30),
            'created_at': claim.service_date,
            'priority': 'High' if claim.status == 'Denied' else 'Medium',
        })

    # Apply additional filters to our task list
    if category_filter:
        tasks = [t for t in tasks if t['category'] == category_filter]
    if task_type_filter:
        tasks = [t for t in tasks if t['task_type'] == task_type_filter]
    if status_filter:
        tasks = [t for t in tasks if t['status'] == status_filter]

    context = {
        'tasks': tasks,
        'task_status_choices': [
            ('Open', 'Open'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed'),
        ],
        'task_category_choices': [
            ('Billing', 'Billing'),
            ('Coding', 'Coding'),
            ('Follow Up', 'Follow Up'),
        ],
        'task_type_choices': [
            ('Claim Review', 'Claim Review'),
            ('Payment Follow Up', 'Payment Follow Up'),
            ('Denial Management', 'Denial Management'),
        ],
        'assigned_users': [],  # Can populate if you have assignment logic
    }
    return render(request, 'main/tasks.html', context)

def task_detail(request, claim_id):
    claim = get_object_or_404(Claim, id=claim_id)
    
    # Convert claim to task
    if claim.status == 'Denied':
        task_type = 'Denial Management'
        category = 'Billing'
    elif claim.status == 'Pending':
        task_type = 'Claim Review'
        category = 'Coding'
    else:
        task_type = 'Payment Follow Up'
        category = 'Billing'
    
    task = {
        'id': claim.id,
        'title': f"{claim.status} - {claim.patient_name}",
        'description': f"Action needed for claim {claim.id}",
        'status': 'Open',
        'category': category,
        'task_type': task_type,
        'priority': 'High' if claim.status == 'Denied' else 'Medium',
        'claim': claim,
        'created_at': claim.service_date,
        'due_date': claim.service_date + timedelta(days=30),
    }
    
    return render(request, 'main/task_detail.html', {'task': task})

def task_detail(request, task_id):
    task = get_object_or_404(Task.objects.select_related('claim', 'patient'), id=task_id)
    return render(request, 'main/task_detail.html', {'task': task})

def task_detail(request, task_id):
    tasks = get_tasks()
    task = next((t for t in tasks if t['id'] == int(task_id)), None)
    
    if not task:
        raise Http404("Task not found")
    
    # Link with claim if exists
    claim = None
    if task.get('claim_id'):
        try:
            claim = Claim.objects.get(id=task['claim_id'])
        except Claim.DoesNotExist:
            pass
    
    context = {
        'task': task,
        'claim': claim
    }
    return render(request, 'main/task_detail.html', context)