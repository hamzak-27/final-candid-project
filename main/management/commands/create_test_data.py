from django.core.management.base import BaseCommand
from main.models import Claim
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Creates test data for the Candid Health claims app'

    def handle(self, *args, **kwargs):
        # Clear existing claims
        Claim.objects.all().delete()
        
        # Patient names
        patient_names = [
            "FRANCISCA DIAZ", "LINDA KANG", "PAULINO ALCAYAGA", "GIUSEPPA ROMANO",
            "ROBERTA FIAMMETTA", "CARMELLA PRAINO", "EILEEN EBNER", "IRMGARD RODRIGUEZ",
            "SHIRLEY SALAMAN", "ERNEST LAUTH"
        ]
        
        # Payer options
        payer_options = [
            {"name": "NEW YORK MEDICARE GHI", "id": "13292"},
            {"name": "CIGNA", "id": "62308"},
            {"name": "UNITED HEALTHCARE", "id": "87726"},
        ]
        
        # Status options (weighted towards 'Submitted to Payer')
        status_options = [
            ('Submitted to Payer', 0.7),
            ('Pending', 0.1),
            ('Approved', 0.1),
            ('Denied', 0.1),
        ]
        
        # Create 10 claims
        for i in range(10):
            # Random service date within past 30 days
            service_date = datetime.now() - timedelta(days=random.randint(1, 30))
            
            # Random payer
            payer = random.choice(payer_options)
            
            # Weighted random status
            status = random.choices(
                [s[0] for s in status_options],
                weights=[s[1] for s in status_options],
                k=1
            )[0]
            
            # Random billed amount between $100 and $300
            billed_amount = round(random.uniform(100, 300), 2)
            
            # Create claim
            claim = Claim.objects.create(
                patient_name=patient_names[i],
                service_date=service_date,
                payer_name=payer["name"],
                payer_id=payer["id"],
                status=status,
                billed_amount=billed_amount,
                allowed_amount=0.00,
                insurance_paid=0.00,
                patient_responsibility=0.00,
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created claim for {claim.patient_name}'))
            
        self.stdout.write(self.style.SUCCESS('Successfully created test data')) 