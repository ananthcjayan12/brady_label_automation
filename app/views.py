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
import tempfile
from django.utils import timezone
from .models import Label, ExcelConfiguration
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
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

# Register Arial font
font_path_arial = os.path.join(settings.STATIC_ROOT, 'fonts', 'Arial.ttf')
font_path_arial_bold = os.path.join(settings.STATIC_ROOT, 'fonts', 'ArialBold.ttf')
pdfmetrics.registerFont(TTFont('Arial', font_path_arial))
pdfmetrics.registerFont(TTFont('ArialBold', font_path_arial_bold))
# Assuming the Excel file is in the same directory as manage.py
EXCEL_FILE_PATH = os.path.join(settings.BASE_DIR, 'barcode_data.xlsx')

# Create your views here.

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['excel_path'] = ExcelConfiguration.get_excel_path()
        return context

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
@csrf_exempt
def process_barcode(request):
    if request.method == 'POST':
        barcode = request.POST.get('barcode', '')
        stage = request.POST.get('stage', '')
        should_print = request.POST.get('print', 'false').lower() == 'true'

        if stage == 'first-stage':
            response_data = process_first_stage(request)
        elif stage == 'second-stage':
            response_data = process_second_stage(request)
        else:
            return JsonResponse({'error': 'Invalid stage'}, status=400)

        if should_print and response_data.get('success', False):
            print_success, print_message = print_label(response_data.get('label_pdf', ''), request.user, barcode)
            response_data['print_success'] = print_success
            response_data['print_message'] = print_message

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def process_first_stage(request):
    barcode = request.POST.get('barcode', '')
    custom_text = request.POST.get('custom_text', '')
    try:
        label, created = Label.objects.get_or_create(
            barcode=barcode,
            defaults={'stage': 'first', 'custom_text': custom_text}
        )
        if not created:
            label.custom_text = custom_text
            label.save()
        label_content, label_pdf_base64 = generate_first_stage_label(barcode, custom_text)
        return {
            'success': True,
            'message': 'Label generated successfully',
            'label_content': label_content,
            'label_pdf': label_pdf_base64,
            'barcode': barcode,
            'custom_text': custom_text
        }
    except IntegrityError:
        return {
            'success': False,
            'error': 'A label with this barcode already exists',
            'barcode': barcode
        }

def process_second_stage(request):
    try:
        barcode = request.POST.get('barcode', '')
        model = request.POST.get('model', '')
        fcc_id = request.POST.get('fcc_id', '')
        email = request.POST.get('email', '')
        logo = request.FILES.get('logo')
        fc_logo = request.FILES.get('fc_logo')
        font_size = float(request.POST.get('font_size', 4.5))  # Get font size, default to 4.5 if not provided

        logger.debug(f"Excel file path: {EXCEL_FILE_PATH}")
        logger.debug(f"Excel file exists: {os.path.exists(EXCEL_FILE_PATH)}")

        # Read the Excel file
        df = pd.read_excel(EXCEL_FILE_PATH, dtype={
            'barcode_number': str, 
            'sr_number': str, 
            'CELL_Info.imei': str
        }, na_values=['NA'], keep_default_na=False)
        
        logger.debug(f"Excel file read successfully. Columns: {df.columns.tolist()}")
        
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
        label_content, label_pdf_base64 = generate_second_stage_label(
            label.serial_number, 
            label.imei_number, 
            model, 
            fcc_id, 
            email, 
            logo, 
            fc_logo,
            font_size  # Pass font size to the label generation function
        )
        
        return {
            'success': True,
            'message': 'Label generated successfully',
            'label_content': label_content,
            'label_pdf': label_pdf_base64,
            'serial_number': label.serial_number,
            'imei_number': label.imei_number,
        }
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {str(e)}")
        return {'error': f'Excel file not found: {str(e)}', 'success': False}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {'error': f'An unexpected error occurred: {str(e)}', 'success': False}

def generate_first_stage_label(barcode, custom_text):
    buffer = BytesIO()
    
    # Create the PDF object, using BytesIO as its "file."
    c = canvas.Canvas(buffer, pagesize=(19.05*mm, 6.35*mm))
    
    # Draw border with rounded corners
    c.roundRect(0.2*mm, 0.2*mm, 18.65*mm, 5.95*mm, radius=0.5*mm)  # Added border
    
    # Calculate available space
    total_height = 6.35*mm
    total_width = 19.05*mm
    margin = 0.5*mm
    available_height = total_height - (2 * margin)
    
    # Set consistent font size for both top and bottom text
    font_size = 3
    
    # Draw the custom text if provided
    if custom_text:
        c.setFont("Arial", font_size)
        text_height = 1.5*mm  # Height for custom text
        
        # Calculate text width to center it
        text_width = c.stringWidth(custom_text, "Arial", font_size)
        text_x = (total_width - text_width) / 2  # Center the text horizontally
        text_y = total_height - margin - 1*mm  # Position from top with margin
        
        # Draw the centered text
        c.drawString(text_x, text_y, custom_text)
    else:
        text_height = 0
    
    # Generate and draw the barcode (reduced size)
    barcode_height = 3*mm  # Reduced height
    barcode_obj = code128.Code128(barcode, barWidth=0.18*mm, barHeight=barcode_height)  # Reduced bar width
    barcode_width = barcode_obj.width
    barcode_x = (total_width - barcode_width) / 2  # Center the barcode horizontally
    barcode_y = margin + 1.5*mm  # Adjusted position to center vertically
    barcode_obj.drawOn(c, barcode_x, barcode_y-0.5*mm)
    
    # Draw the barcode number with same font size as top text
    c.setFont("Arial", font_size)  # Same font size as custom text
    text_width = c.stringWidth(barcode, "Arial", font_size)
    text_x = (total_width - text_width) / 2  # Center the text horizontally
    c.drawString(text_x, margin, barcode)
    
    # Close the PDF object cleanly, and we're done.
    c.showPage()
    c.save()
    
    # Get the value of the BytesIO buffer and encode it to base64
    pdf = buffer.getvalue()
    buffer.close()
    pdf_base64 = base64.b64encode(pdf).decode()
    
    return f"Barcode: {barcode}, Custom Text: {custom_text}", f"data:application/pdf;base64,{pdf_base64}"

def generate_second_stage_label(serial_number, imei_number, model, fcc_id, email, logo, fc_logo, font_size):
    buffer = BytesIO()
    
    # Create the PDF object, using BytesIO as its "file."
    c = canvas.Canvas(buffer, pagesize=(100*mm, 25*mm))
    
    # Draw border with rounded corners
    c.roundRect(0.5*mm, 0.5*mm, 99*mm, 24*mm, radius=1*mm)  # Added border
    
    # Set font to Arial and use the provided font size
    c.setFont("Arial", font_size)
    
    # Handle logo (use default if none provided)
    try:
        if logo:
            logo_path = os.path.join(settings.MEDIA_ROOT, 'temp_logo.png')
            with open(logo_path, 'wb+') as destination:
                for chunk in logo.chunks():
                    destination.write(chunk)
        else:
            # Use default logo
            logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'default_logo.png')
        
        # Draw the logo
        c.drawImage(logo_path, 6*mm, 3.8*mm, width=15*mm, height=30*mm, preserveAspectRatio=True)
        
        # Clean up temporary file if it was created
        if logo:
            os.remove(logo_path)
            
    except Exception as e:
        logger.error(f"Error processing main logo: {str(e)}")

    # Draw the model and FCC ID
    c.setFont("ArialBold", font_size)
    c.drawString(8.1*mm, 10*mm, "Model: ")
    c.setFont("Arial", font_size)
    c.drawString(8.1*mm + c.stringWidth("Model: ", "ArialBold", font_size), 10*mm, model)

    # Draw the FCC ID
    c.setFont("ArialBold", font_size)
    c.drawString(8.1*mm, 7*mm, "FCC ID: ")
    c.setFont("Arial", font_size)
    c.drawString(8.1*mm + c.stringWidth("FCC ID: ", "ArialBold", font_size), 7*mm, fcc_id)

    # Draw the IMEI
    c.setFont("ArialBold", font_size)
    c.drawString(8.1*mm, 4*mm, "IMEI: ")
    c.setFont("Arial", font_size)
    c.drawString(8.1*mm + c.stringWidth("IMEI: ", "ArialBold", font_size), 4*mm, imei_number)

    # Draw the SN
    c.setFont("ArialBold", font_size)
    c.drawString(38.7*mm, 23*mm, "SN: ")
    c.setFont("Arial", font_size)
    c.drawString(38.7*mm + c.stringWidth("SN: ", "ArialBold", font_size), 23*mm, serial_number)
    
    # Generate and draw the barcode
    barcode = code128.Code128(serial_number, barWidth=0.26*mm, barHeight=10*mm)
    barcode.drawOn(c, 31.7*mm, 11*mm)
    
    # Draw the email
    c.drawString(38.7*mm, 8*mm, email)
    
    # Handle FC logo (use default if none provided)
    try:
        if fc_logo:
            fc_logo_path = os.path.join(settings.MEDIA_ROOT, 'temp_fc_logo.png')
            with open(fc_logo_path, 'wb+') as destination:
                for chunk in fc_logo.chunks():
                    destination.write(chunk)
        else:
            # Use default FC logo
            fc_logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'default_fc_logo.png')
        
        # Draw the FC logo
        c.drawImage(fc_logo_path, 85*mm, 2*mm, width=8*mm, height=8*mm)
        
        # Clean up temporary file if it was created
        if fc_logo:
            os.remove(fc_logo_path)
            
    except Exception as e:
        logger.error(f"Error processing FC logo: {str(e)}")
    
    # Close the PDF object cleanly, and we're done.
    c.showPage()
    c.save()
    
    # Get the value of the BytesIO buffer and encode it to base64
    pdf = buffer.getvalue()
    buffer.close()
    pdf_base64 = base64.b64encode(pdf).decode()
    
    return f"SN: {serial_number}, IMEI: {imei_number}", f"data:application/pdf;base64,{pdf_base64}"

def print_label(label_pdf_base64, user, barcode):
    try:
        # Update the label's print status and user in the database
        label = Label.objects.get(barcode=barcode)
        label.is_printed = True
        label.printed_at = timezone.now()
        label.printed_by = user
        label.save()

        return True, "Label ready for printing"
    except Exception as e:
        return False, f"Error updating label status: {str(e)}"

@login_required
def preview_label(request, label_id):
    try:
        label = Label.objects.get(id=label_id)
        if label.stage == 'first':
            label_content, label_pdf_base64 = generate_first_stage_label(label.barcode, label.custom_text)
        else:
            # For second stage, we need to fetch data from Excel
            df = pd.read_excel(EXCEL_FILE_PATH, dtype={
                'barcode_number': str, 
                'sr_number': str, 
                'CELL_Info.imei': str
            }, na_values=['NA'], keep_default_na=False)
            
            # Find the row with matching barcode_number
            data = df[df['barcode_number'].str.strip() == label.barcode.strip()]
            
            if data.empty:
                return JsonResponse({
                    'success': False,
                    'error': 'Barcode not found in Excel'
                }, status=404)
            
            data = data.iloc[0]
            # Use default values for optional parameters
            label_content, label_pdf_base64 = generate_second_stage_label(
                label.serial_number,
                label.imei_number,
                "0124-010",  # default model
                "2BFGFWTX1",  # default FCC ID
                "contact@waveinnova.com",  # default email
                None,  # no custom logo
                None,  # no custom FC logo
                4.5   # default font size
            )
        
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
        logger.error(f"Error in preview_label: {str(e)}")  # Add logging
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
            df = pd.read_excel(EXCEL_FILE_PATH, dtype={
                'barcode_number': str, 
                'sr_number': str, 
                'CELL_Info.imei': str
            }, na_values=['NA'], keep_default_na=False)
            
            # Find the row with matching barcode_number
            data = df[df['barcode_number'].str.strip() == label.barcode.strip()]
            
            if data.empty:
                return JsonResponse({
                    'success': False,
                    'error': 'Barcode not found in Excel'
                }, status=404)
            
            data = data.iloc[0]
            label_content, label_pdf_base64 = generate_second_stage_label(label.serial_number, data)
        
        print_success, print_message = print_label(label_pdf_base64, request.user, label.barcode)
        
        if print_success:
            label.is_printed = True
            label.printed_at = timezone.now()
            label.printed_by = request.user
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

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

@login_required
def update_excel_path(request):
    if request.method == 'POST':
        new_path = request.POST.get('excel_path')
        if new_path:
            config = ExcelConfiguration.objects.first()
            if not config:
                config = ExcelConfiguration()
            config.excel_path = new_path
            config.updated_by = request.user
            config.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'No path provided'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

