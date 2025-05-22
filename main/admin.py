from django.contrib import admin
from .models import Claim

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'service_date', 'payer_name', 'payer_id', 'status', 'billed_amount')
    list_filter = ('status', 'payer_name')
    search_fields = ('patient_name', 'payer_name', 'payer_id')
    date_hierarchy = 'service_date'
