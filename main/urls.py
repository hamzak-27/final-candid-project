from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('claims/', views.claims, name='claims'),
    path('claims/<int:claim_id>/', views.claim_detail, name='claim_detail'),
    path('patients/<str:external_patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/', views.patients, name='patients'),
]
