from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from reportlab.lib.pagesizes import mm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
import base64
import pandas as pd
import os
import cups
import tempfile
from django.utils import timezone
from .models import Label
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from reportlab.lib.pagesizes import mm
from reportlab.graphics.barcode import code128
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Arial font
pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))

# Assuming the Excel file is in the same directory as manage.py
EXCEL_FILE_PATH = 'barcode_data.xlsx'

# Create your views here.

class HomeView(TemplateView):
    template_name = 'home.html'

class FirstStageView(TemplateView):
    template_name = 'first_stage.html'

class SecondStageView(TemplateView):
    template_name = 'second_stage.html'

@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_labels'] = Label.objects.count()
        context['printed_labels'] = Label.objects.filter(is_printed=True).count()
        context['first_stage_labels'] = Label.objects.filter(stage='first').count()
        context['second_stage_labels'] = Label.objects.filter(stage='second').count()

        context['labels_by_day'] = Label.objects.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('-day')[:7]

        context['recent_labels'] = Label.objects.order_by('-created_at')[:10]

        return context

def excel_lookup(request):
    serial_number = request.GET.get('serial_number', '')
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        print(f"Excel columns: {df.columns.tolist()}")  # Debug print
        if 'Serial Number' not in df.columns:
            return JsonResponse({'error': 'Serial Number column not found in Excel'}, status=400)
        row = df[df['Serial Number'] == serial_number]
        if row.empty:
            return JsonResponse({'error': 'Serial number not found'}, status=404)
        row = row.iloc[0]
        return JsonResponse({
            'imei_number': row.get('IMEI Number', 'N/A'),
            'unique_number': row.get('Unique Number', 'N/A'),
            'is_printed': row.get('Is Printed', False)
        })
    except FileNotFoundError:
        return JsonResponse({'error': 'Excel file not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

def update_print_status(request):
    serial_number = request.POST.get('serial_number', '')
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        if 'Serial Number' not in df.columns:
            return JsonResponse({'error': 'Serial Number column not found in Excel'}, status=400)
        mask = df['Serial Number'] == serial_number
        if not mask.any():
            return JsonResponse({'error': 'Serial number not found'}, status=404)
        df.loc[mask, 'Is Printed'] = True
        df.to_excel(EXCEL_FILE_PATH, index=False)
        return JsonResponse({'success': True})
    except FileNotFoundError:
        return JsonResponse({'error': 'Excel file not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

@login_required
def process_barcode(request):
    scanned_barcode = request.POST.get('barcode', '')
    stage = request.POST.get('stage', '')
    should_print = request.POST.get('print', 'false').lower() == 'true'

    if stage == 'first-stage':
        response_data = process_first_stage(scanned_barcode)
    elif stage == 'second-stage':
        response_data = process_second_stage(scanned_barcode)
    else:
        return JsonResponse({'error': 'Invalid stage'}, status=400)

    if should_print and response_data.get('success', False):
        print_success, print_message = print_label(response_data.get('label_pdf', ''), request.user)
        response_data['print_success'] = print_success
        response_data['print_message'] = print_message

    return JsonResponse(response_data)

def process_first_stage(barcode):
    try:
        label, created = Label.objects.get_or_create(
            barcode=barcode,
            defaults={'stage': 'first'}
        )
        label_content, label_pdf_base64 = generate_first_stage_label(barcode)
        return {
            'success': True,
            'message': 'Label generated successfully',
            'label_content': label_content,
            'label_pdf': label_pdf_base64,
            'barcode': barcode
        }
    except IntegrityError:
        return {
            'success': False,
            'error': 'A label with this barcode already exists',
            'barcode': barcode
        }

def process_second_stage(barcode):
    try:
        # Read the Excel file
        df = pd.read_excel(EXCEL_FILE_PATH, dtype={
            'barcode_number': str, 
            'sr_number': str, 
            'CELL_Info.imei': str
        }, na_values=['NA'], keep_default_na=False)
        
        # Ensure required columns exist
        required_columns = ['barcode_number', 'sr_number', 'CELL_Info.imei']
        for column in required_columns:
            if column not in df.columns:
                return {'error': f'{column} column not found in Excel', 'success': False}
        
        # Strip leading and trailing spaces from the input barcode
        stripped_barcode = barcode.strip()
        
        # Find the row with matching barcode_number
        data = df[df['barcode_number'].str.strip() == stripped_barcode]
        
        if data.empty:
            return {'error': 'Barcode not found in Excel', 'success': False}
        
        data = data.iloc[0]
        
        label, created = Label.objects.get_or_create(
            barcode=stripped_barcode,
            defaults={
                'stage': 'second',
                'serial_number': str(data.get('sr_number', 'N/A')).strip(),
                'imei_number': str(data.get('CELL_Info.imei', 'N/A')).strip(),
            }
        )

        if not created:
            # Update existing label if it wasn't just created
            label.serial_number = str(data.get('sr_number', 'N/A')).strip()
            label.imei_number = str(data.get('CELL_Info.imei', 'N/A')).strip()
            label.save()

        label_content, label_pdf_base64 = generate_second_stage_label(label.serial_number, data)
        
        return {
            'success': True,
            'message': 'Label generated successfully',
            'label_content': label_content,
            'label_pdf': label_pdf_base64,
            'serial_number': label.serial_number,
            'imei_number': label.imei_number,
        }
    except FileNotFoundError:
        return {'error': 'Excel file not found', 'success': False}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}', 'success': False}

def generate_first_stage_label(barcode):
    buffer = BytesIO()
    
    # Create the PDF object, using BytesIO as its "file."
    c = canvas.Canvas(buffer, pagesize=(19.05*mm, 6.35*mm))
    
    # Leave space for the title (about 1/3 of the label height)
    usable_height = 4.23*mm  # 2/3 of 6.35mm
    
    # Generate and draw the barcode
    barcode_height = usable_height * 0.7  # 70% of usable height for barcode
    barcode_obj = code128.Code128(barcode, barWidth=0.15*mm, barHeight=barcode_height)
    barcode_width = barcode_obj.width
    barcode_x = (19.05*mm - barcode_width) / 2  # Center the barcode horizontally
    barcode_y = 6.35*mm - usable_height  # Position at the bottom of usable area
    barcode_obj.drawOn(c, barcode_x, barcode_y)
    
    # Draw the barcode number
    c.setFont("Arial", 4)  # Set font to Arial, size 6
    text_width = c.stringWidth(barcode, "Arial", 4)
    text_x = (19.05*mm - text_width) / 2  # Center the text horizontally
    c.drawString(text_x, 0.5*mm, barcode)
    
    # Close the PDF object cleanly, and we're done.
    c.showPage()
    c.save()
    
    # Get the value of the BytesIO buffer and encode it to base64
    pdf = buffer.getvalue()
    buffer.close()
    pdf_base64 = base64.b64encode(pdf).decode()
    
    return f"Barcode: {barcode}", f"data:application/pdf;base64,{pdf_base64}"

def generate_second_stage_label(serial_number, data):
    buffer = BytesIO()
    
    # Create the PDF object, using BytesIO as its "file."
    c = canvas.Canvas(buffer, pagesize=(100*mm, 25*mm))
    
    # Set font to Arial and size to 6px (approximately 4.5 points)
    c.setFont("Arial", 4.5)
    
    # Draw the SN
    sn_x = 41.7*mm
    sn_y = (25-3)*mm
    c.drawString(sn_x, sn_y, f"{serial_number}")
    
    # Generate and draw the barcode
    barcode = code128.Code128(serial_number, barWidth=0.26*mm, barHeight=7*mm)
    barcode_y = 13*mm  # Positioned just below SN
    barcode.drawOn(c, 30.7*mm, barcode_y)  # Use the same x-coordinate as SN
    
    # Draw the IMEI
    imei_number = str(data.get('CELL_Info.imei', 'N/A')).strip()
    c.drawString(13.4*mm, (25-19.3)*mm, f"{imei_number}")
    
    # Close the PDF object cleanly, and we're done.
    c.showPage()
    c.save()
    
    # Get the value of the BytesIO buffer and encode it to base64
    pdf = buffer.getvalue()
    buffer.close()
    pdf_base64 = base64.b64encode(pdf).decode()
    
    return f"SN: {serial_number}, IMEI: {imei_number}", f"data:application/pdf;base64,{pdf_base64}"

def print_label(label_pdf_base64, user):
    try:
        # Remove the data:application/pdf;base64, prefix
        pdf_data = base64.b64decode(label_pdf_base64.split(',')[1])

        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_data)
            temp_file_path = temp_file.name

        # Connect to CUPS
        conn = cups.Connection()
        printers = conn.getPrinters()
        
        if not printers:
            return False, "No printers found"

        # Get the default printer
        default_printer = conn.getDefault()
        if not default_printer:
            # If no default printer, use the first available printer
            default_printer = list(printers.keys())[0]

        # Print 2 copies
        copies = 2
        print_options = {
            "copies": str(copies)
        }

        # Send print job
        job_id = conn.printFile(default_printer, temp_file_path, "Label Print Job", print_options)

        # Clean up the temporary file
        os.unlink(temp_file_path)

        # Update the label's print status and user in the database
        label = Label.objects.get(barcode=barcode)
        label.is_printed = True
        label.printed_at = timezone.now()
        label.printed_by = user
        label.save()

        return True, f"Print job sent successfully. Job ID: {job_id}"
    except Exception as e:
        return False, f"Error printing label: {str(e)}"

@login_required
def preview_label(request, label_id):
    try:
        label = Label.objects.get(id=label_id)
        if label.stage == 'first':
            label_content, label_pdf_base64 = generate_first_stage_label(label.barcode)
        else:
            # For second stage, we need to fetch data from Excel
            df = pd.read_excel(EXCEL_FILE_PATH)
            data = df[df['Serial Number'] == label.barcode].iloc[0]
            label_content, label_pdf_base64 = generate_second_stage_label(label.barcode, data)
        
        return JsonResponse({
            'success': True,
            'label_pdf': label_pdf_base64
        })
    except Label.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Label not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def reprint_label(request, label_id):
    try:
        label = Label.objects.get(id=label_id)
        if label.stage == 'first':
            label_content, label_pdf_base64 = generate_first_stage_label(label.barcode)
        else:
            # For second stage, we need to fetch data from Excel
            df = pd.read_excel(EXCEL_FILE_PATH)
            data = df[df['Serial Number'] == label.barcode].iloc[0]
            label_content, label_pdf_base64 = generate_second_stage_label(label.barcode, data)
        
        print_success, print_message = print_label(label_pdf_base64, request.user)
        
        if print_success:
            label.is_printed = True
            label.printed_at = timezone.now()
            label.save()
        
        return JsonResponse({
            'success': print_success,
            'message': print_message
        })
    except Label.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Label not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

