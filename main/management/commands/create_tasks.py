from django.core.management.base import BaseCommand
from main.models import Task, Claim, Patient
from django.utils import timezone
from datetime import timedelta
from django.db import models

class Command(BaseCommand):
    help = 'Creates tasks based on existing claims and patients data'

    def handle(self, *args, **kwargs):
        # Get all claims that need attention
        pending_claims = Claim.objects.filter(status='Pending')
        denied_claims = Claim.objects.filter(status='Denied')
        submitted_claims = Claim.objects.filter(status='Submitted to Payer')

        # Create tasks for denied claims
        for claim in denied_claims:
            Task.objects.create(
                title=f'Review Denied Claim - {claim.get_patient_name}',
                description=f'Investigate and appeal denied claim for {claim.get_patient_name}. Claim date: {claim.service_date}',
                status='Open',
                category='Billing',
                task_type='Denial Management',
                priority='High',
                assigned_to='Billing Team',
                due_date=timezone.now().date() + timedelta(days=2),
                claim=claim,
                patient=claim.patient
            )

        # Create tasks for pending claims that are older than 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        old_pending_claims = pending_claims.filter(service_date__lt=thirty_days_ago)
        
        for claim in old_pending_claims:
            Task.objects.create(
                title=f'Follow up on Pending Claim - {claim.get_patient_name}',
                description=f'Follow up on pending claim from {claim.service_date} for {claim.get_patient_name}',
                status='Open',
                category='Follow Up',
                task_type='Payment Follow Up',
                priority='Medium',
                assigned_to='Follow-up Team',
                due_date=timezone.now().date() + timedelta(days=5),
                claim=claim,
                patient=claim.patient
            )

        # Create tasks for claims that need coding review
        for claim in submitted_claims:
            Task.objects.create(
                title=f'Review Claim Coding - {claim.get_patient_name}',
                description=f'Verify CPT and ICD codes for claim from {claim.service_date}',
                status='Open',
                category='Coding',
                task_type='Claim Review',
                priority='Medium',
                assigned_to='Coding Team',
                due_date=timezone.now().date() + timedelta(days=3),
                claim=claim,
                patient=claim.patient
            )

        # Create tasks for patients with multiple claims
        patients_with_multiple_claims = Patient.objects.annotate(
            claim_count=models.Count('claim')
        ).filter(claim_count__gt=2)

        for patient in patients_with_multiple_claims:
            Task.objects.create(
                title=f'Review Patient Claims History - {patient.full_name}',
                description=f'Review claims history and payment patterns for {patient.full_name}',
                status='Open',
                category='Billing',
                task_type='Claim Review',
                priority='Medium',
                assigned_to='Billing Team',
                due_date=timezone.now().date() + timedelta(days=7),
                patient=patient
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully created tasks based on existing data')
        ) 