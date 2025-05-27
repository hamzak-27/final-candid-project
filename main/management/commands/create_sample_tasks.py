from django.core.management.base import BaseCommand
from main.models import Task, Claim, Patient
from django.utils import timezone
from random import choice

class Command(BaseCommand):
    help = 'Create sample Task objects for testing task detail page.'

    def handle(self, *args, **kwargs):
        claims = list(Claim.objects.all())
        patients = list(Patient.objects.all())
        if not claims or not patients:
            self.stdout.write(self.style.ERROR('You need at least one Claim and one Patient in the database.'))
            return
        for i in range(1, 6):
            claim = choice(claims)
            patient = claim.patient if claim.patient else choice(patients)
            task = Task.objects.create(
                title=f'Sample Task {i}',
                description='This is a sample task for testing.',
                status='Open',
                category='Billing',
                task_type='Claim Review',
                priority='Medium',
                assigned_to='person1',
                due_date=timezone.now().date(),
                claim=claim,
                patient=patient
            )
            self.stdout.write(self.style.SUCCESS(f'Created task: {task.title} (ID: {task.id})')) 