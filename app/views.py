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

# Assuming the Excel file is in the same directory as manage.py
EXCEL_FILE_PATH = 'barcode_data.xlsx'

# Create your views here.

class HomeView(TemplateView):
    template_name = 'home.html'

class FirstStageView(TemplateView):
    template_name = 'first_stage.html'

class SecondStageView(TemplateView):
    template_name = 'second_stage.html'

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
        print_success, print_message = print_label(response_data.get('label_pdf', ''))
        response_data['print_success'] = print_success
        response_data['print_message'] = print_message

    return JsonResponse(response_data)

def process_first_stage(barcode):
    label_content, label_pdf_base64 = generate_first_stage_label(barcode)
    return {
        'success': True,
        'message': 'Label generated successfully',
        'label_content': label_content,
        'label_pdf': label_pdf_base64,
        'barcode': barcode  # Add this line to include the barcode in the response
    }

def process_second_stage(barcode):
    try:
        # Read the Excel file, treating NA values in 'Is Printed' column as False
        df = pd.read_excel(EXCEL_FILE_PATH, dtype={
            'Serial Number': str, 
            'IMEI Number': str, 
            'Unique Number': str
        }, na_values=['NA'], keep_default_na=False)
        
        # Fill NA values in 'Is Printed' column with False
        if 'Is Printed' in df.columns:
            df['Is Printed'] = df['Is Printed'].fillna(False)
        else:
            df['Is Printed'] = False

        if 'Serial Number' not in df.columns:
            return {'error': 'Serial Number column not found in Excel', 'success': False}
        
        # Strip leading and trailing spaces from the input barcode
        stripped_barcode = barcode.strip()
        
        # Strip spaces from 'Serial Number' column and compare with stripped barcode
        data = df[df['Serial Number'].str.strip() == stripped_barcode]
        
        if data.empty:
            return {'error': 'Barcode not found in Excel', 'success': False}
        
        data = data.iloc[0]
        label_content, label_pdf_base64 = generate_second_stage_label(stripped_barcode, data)
        
        # Update the 'Is Printed' status in the Excel file
        df.loc[df['Serial Number'].str.strip() == stripped_barcode, 'Is Printed'] = True
        df.to_excel(EXCEL_FILE_PATH, index=False)
        
        return {
            'success': True,
            'message': 'Label generated successfully',
            'label_content': label_content,
            'label_pdf': label_pdf_base64,
            'serial_number': str(data.get('Serial Number', 'N/A')).strip(),
            'imei_number': str(data.get('IMEI Number', 'N/A')).strip(),
            'unique_number': str(data.get('Unique Number', 'N/A')).strip()
        }
    except FileNotFoundError:
        return {'error': 'Excel file not found', 'success': False}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}', 'success': False}

def generate_first_stage_label(barcode):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=(100*mm, 100*mm))
    
    # Add barcode
    qr = QrCodeWidget(barcode)
    bounds = qr.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(45*mm, 45*mm, transform=[45*mm/width,0,0,45*mm/height,0,0])
    d.add(qr)
    renderPDF.draw(d, p, 15*mm, 40*mm)

    # Add text
    p.setFont("Helvetica", 12)
    p.drawString(15*mm, 30*mm, f"Barcode: {barcode}")

    p.showPage()
    p.save()

    pdf_bytes = buffer.getvalue()
    pdf_base64 = base64.b64encode(pdf_bytes).decode()

    return f"Barcode: {barcode}", f"data:application/pdf;base64,{pdf_base64}"

def generate_second_stage_label(barcode, data):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=(100*mm, 100*mm))
    
    # Add barcode
    qr = QrCodeWidget(barcode)
    bounds = qr.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(45*mm, 45*mm, transform=[45*mm/width,0,0,45*mm/height,0,0])
    d.add(qr)
    renderPDF.draw(d, p, 15*mm, 40*mm)

    # Add text
    p.setFont("Helvetica", 10)
    p.drawString(15*mm, 30*mm, f"Barcode: {barcode}")
    p.drawString(15*mm, 25*mm, f"Serial: {str(data.get('Serial Number', 'N/A')).strip()}")
    p.drawString(15*mm, 20*mm, f"IMEI: {str(data.get('IMEI Number', 'N/A')).strip()}")
    p.drawString(15*mm, 15*mm, f"Unique: {str(data.get('Unique Number', 'N/A')).strip()}")

    p.showPage()
    p.save()

    pdf_bytes = buffer.getvalue()
    pdf_base64 = base64.b64encode(pdf_bytes).decode()

    label_content = f"""
    Barcode: {barcode}
    Serial Number: {str(data.get('Serial Number', 'N/A')).strip()}
    IMEI Number: {str(data.get('IMEI Number', 'N/A')).strip()}
    Unique Number: {str(data.get('Unique Number', 'N/A')).strip()}
    """

    return label_content, f"data:application/pdf;base64,{pdf_base64}"

def print_label(label_pdf_base64):
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

        return True, f"Print job sent successfully. Job ID: {job_id}"
    except Exception as e:
        return False, f"Error printing label: {str(e)}"
