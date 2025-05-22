from django.shortcuts import render, get_object_or_404, redirect
from .models import Claim
from django import forms
from django.db.models import Count

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
