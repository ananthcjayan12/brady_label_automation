from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ExcelData(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    imei_number = models.CharField(max_length=100)
    unique_number = models.CharField(max_length=100)
    is_printed = models.BooleanField(default=False)

    def __str__(self):
        return f"Serial: {self.serial_number}, IMEI: {self.imei_number}"

class Label(models.Model):
    STAGE_CHOICES = [
        ('first', 'First Stage'),
        ('second', 'Second Stage'),
    ]
    barcode = models.CharField(max_length=100, unique=True)
    stage = models.CharField(max_length=10, choices=STAGE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    is_printed = models.BooleanField(default=False)
    printed_by = models.ForeignKey(User, null=True, blank=True, related_name='printed_labels', on_delete=models.SET_NULL)
    
    # Fields for second stage
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    imei_number = models.CharField(max_length=100, null=True, blank=True)
    # Remove the unique_number field if it's no longer needed
    # unique_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.get_stage_display()} - {self.barcode}"

    class Meta:
        ordering = ['-created_at']
