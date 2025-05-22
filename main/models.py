from django.db import models

# Create your models here.

class Claim(models.Model):
    STATUS_CHOICES = [
        ('Submitted to Payer', 'Submitted to Payer'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
    ]
    
    patient_name = models.CharField(max_length=255)
    service_date = models.DateField()
    payer_name = models.CharField(max_length=255)
    payer_id = models.CharField(max_length=20)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    billed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    insurance_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    patient_responsibility = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.patient_name} - {self.service_date} - {self.payer_name}"

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
    external_patient_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.external_patient_id})"
