from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

# Create your models here.

class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    zip_plus_4 = models.CharField(max_length=4, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    external_patient_id = models.CharField(max_length=100, unique=True, editable=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.external_patient_id})"

    def save(self, *args, **kwargs):
        logger.info(f"Saving patient {self.id if self.id else 'new'}: {self.first_name} {self.last_name}")
        # Ensure the patient name is properly formatted
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        super().save(*args, **kwargs)
        logger.info(f"Saved patient {self.id}")

class Claim(models.Model):
    STATUS_CHOICES = [
        ('Submitted to Payer', 'Submitted to Payer'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    patient_name = models.CharField(max_length=255)  # Keep for backward compatibility
    service_date = models.DateField()
    payer_name = models.CharField(max_length=255)
    payer_id = models.CharField(max_length=20)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    billed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    insurance_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    patient_responsibility = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    @property
    def get_patient_name(self):
        if self.patient:
            return self.patient.full_name
        return self.patient_name
    
    def __str__(self):
        return f"{self.get_patient_name} - {self.service_date} - {self.payer_name}"

    def save(self, *args, **kwargs):
        logger.info(f"Saving claim {self.id if self.id else 'new'}: patient={self.patient}, patient_name={self.patient_name}")
        # Update patient_name if patient is set
        if self.patient:
            self.patient_name = self.patient.full_name
            logger.info(f"Updated patient_name to {self.patient_name}")
        super().save(*args, **kwargs)
        logger.info(f"Saved claim {self.id}")

@receiver(post_save, sender=Patient)
def update_claim_names(sender, instance, **kwargs):
    """Signal to update all claim names when a patient is updated"""
    logger.info(f"Updating claim names for patient {instance.id}")
    updated = Claim.objects.filter(patient=instance).update(patient_name=instance.full_name)
    logger.info(f"Updated {updated} claims for patient {instance.id}")

class Task(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    CATEGORY_CHOICES = [
        ('Billing', 'Billing'),
        ('Coding', 'Coding'),
        ('Follow Up', 'Follow Up'),
        ('Authorization', 'Authorization'),
    ]
    
    TYPE_CHOICES = [
        ('Claim Review', 'Claim Review'),
        ('Payment Follow Up', 'Payment Follow Up'),
        ('Denial Management', 'Denial Management'),
        ('Prior Auth', 'Prior Auth'),
    ]
    
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    assigned_to = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-created_at']

class ActivityLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.timestamp}: {self.message}"
