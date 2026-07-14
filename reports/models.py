from django.db import models
from accounts.models import User
from patients.models import Patient
from tests.models import TestParameter

from django.utils import timezone

class Report(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', related_name='reports')
    # Use DateTimeField defaulting to timezone.now to map DATETIME and allow edits
    report_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default='Pending')  # Draft, Pending, Approved
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=50, default='Pending')
    branch_id = models.IntegerField(default=1)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='approved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Reports'

class ReportParameterResult(models.Model):
    id = models.AutoField(primary_key=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, db_column='report_id', related_name='results')
    parameter = models.ForeignKey(TestParameter, on_delete=models.CASCADE, db_column='parameter_id')
    result_value = models.TextField()

    class Meta:
        db_table = 'Report_Parameter_Results'
