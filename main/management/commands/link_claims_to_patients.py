from django.core.management.base import BaseCommand
from main.models import Claim, Patient

class Command(BaseCommand):
    help = 'Link existing claims to patients'

    def handle(self, *args, **options):
        claims_without_patient = Claim.objects.filter(patient__isnull=True)
        
        for claim in claims_without_patient:
            external_patient_id = f'DiaFref{claim.id}'
            
            # Try to find existing patient
            try:
                patient = Patient.objects.get(external_patient_id=external_patient_id)
            except Patient.DoesNotExist:
                # Create a new patient
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
                self.stdout.write(f'Created patient: {patient}')
            
            # Link claim to patient
            claim.patient = patient
            claim.patient_name = patient.full_name
            claim.save()
            self.stdout.write(f'Linked claim {claim.id} to patient {patient}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully linked {claims_without_patient.count()} claims to patients')
        ) 