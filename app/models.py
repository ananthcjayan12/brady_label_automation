from django.db import models

# Create your models here.

class ExcelData(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    imei_number = models.CharField(max_length=100)
    unique_number = models.CharField(max_length=100)
    is_printed = models.BooleanField(default=False)

    def __str__(self):
        return f"Serial: {self.serial_number}, IMEI: {self.imei_number}"
