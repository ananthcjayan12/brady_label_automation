import openpyxl
from django.core.management.base import BaseCommand
from app.models import ExcelData

class Command(BaseCommand):
    help = 'Import data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        workbook = openpyxl.load_workbook(excel_file)
        sheet = workbook.active

        for row in sheet.iter_rows(min_row=2, values_only=True):
            serial_number, imei_number, unique_number = row[:3]
            ExcelData.objects.update_or_create(
                serial_number=serial_number,
                defaults={
                    'imei_number': imei_number,
                    'unique_number': unique_number
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully imported Excel data'))
