from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ExcelData(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    imei_number = models.CharField(max_length=100)
    unique_number = models.CharField(max_length=100)

    def __str__(self):
        return f"Serial: {self.serial_number}, IMEI: {self.imei_number}"

class Label(models.Model):
    barcode = models.CharField(max_length=100, unique=True)
    stage = models.CharField(max_length=10, choices=[('first', 'First Stage'), ('second', 'Second Stage')])
    custom_text = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Fields for second stage
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    imei_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.get_stage_display()} - {self.barcode}"

    class Meta:
        ordering = ['-created_at']

class ExcelConfiguration(models.Model):
    excel_path = models.CharField(max_length=500, default='Z:\\AEPLV-Production\\Wave Innova\\01-06-2024\\sample_exce.xlsx')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Excel Configuration'
        verbose_name_plural = 'Excel Configuration'

    def __str__(self):
        return f"Excel Path: {self.excel_path}"

    @classmethod
    def get_excel_path(cls):
        config = cls.objects.first()
        if not config:
            config = cls.objects.create(excel_path='Z:\\AEPLV-Production\\Wave Innova\\01-06-2024\\sample_exce.xlsx')
        return config.excel_path
