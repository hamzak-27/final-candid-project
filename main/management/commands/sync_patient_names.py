from django.core.management.base import BaseCommand
from main.models import Claim, Patient

class Command(BaseCommand):
    help = 'Sync patient names across all claims'

    def handle(self, *args, **options):
        # Update all claims to have the correct patient name from their linked patient
        claims_updated = 0
        
        for claim in Claim.objects.filter(patient__isnull=False):
            if claim.patient_name != claim.patient.full_name:
                claim.patient_name = claim.patient.full_name
                claim.save()
                claims_updated += 1
                self.stdout.write(f'Updated claim {claim.id}: {claim.patient_name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully synced {claims_updated} claim names')
        )
        
        # Show current state
        self.stdout.write('\nCurrent patients:')
        for patient in Patient.objects.all():
            claim_count = patient.claim_set.count()
            self.stdout.write(f'  {patient.full_name} ({patient.external_patient_id}) - {claim_count} claims')
        
        self.stdout.write('\nCurrent claims:')
        for claim in Claim.objects.all():
            self.stdout.write(f'  Claim {claim.id}: {claim.get_patient_name} (linked to: {claim.patient.full_name if claim.patient else "None"})') 