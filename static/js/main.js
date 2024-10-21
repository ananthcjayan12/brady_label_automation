// Add your custom JavaScript here
console.log("Main.js loaded");

// You'll add more functionality for barcode scanning and printing here later

function initBarcodeInput(stage) {
    console.log(`Initializing barcode input for ${stage}`);
    const barcodeInput = document.getElementById('barcode-input');
    const printButton = document.getElementById('print-button');
    let lastScannedBarcode = '';

    barcodeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const barcode = this.value.trim();
            if (barcode) {
                console.log(`Barcode scanned: ${barcode}`);
                lastScannedBarcode = barcode;
                processBarcodeBackend(barcode, stage, false);
                this.value = '';
            }
        }
    });

    printButton.addEventListener('click', function() {
        console.log('Print button clicked');
        if (lastScannedBarcode) {
            console.log(`Sending print request for barcode: ${lastScannedBarcode}`);
            processBarcodeBackend(lastScannedBarcode, stage, true);
        } else {
            console.log('No barcode to print');
            alert('Please scan a barcode first');
        }
    });
}

function processBarcodeBackend(barcode, stage, shouldPrint) {
    console.log(`Processing barcode: ${barcode}, Stage: ${stage}, Should Print: ${shouldPrint}`);
    fetch('/process-barcode/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `barcode=${encodeURIComponent(barcode)}&stage=${encodeURIComponent(stage)}&print=${shouldPrint}`
    })
    .then(response => response.json())
    .then(data => {
        console.log('Received response:', data);
        if (data.success) {
            updateUI(data, stage);
            showLabelPreview(data.label_pdf);
            if (shouldPrint) {
                if (data.print_success) {
                    console.log('Print successful:', data.print_message);
                    alert('Label sent to printer: ' + data.print_message);
                } else {
                    console.error('Print failed:', data.print_message);
                    alert('Error printing label: ' + data.print_message);
                }
            } else {
                alert(data.message);
            }
        } else {
            console.error('Error:', data.error);
            alert('Error: ' + (data.error || 'Unknown error occurred'));
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        alert('An error occurred while processing the barcode');
    });
}

function updateUI(data, stage) {
    console.log('Updating UI with data:', data);
    const scannedResult = document.getElementById('scanned-result');
    if (scannedResult) {
        scannedResult.textContent = data.barcode || data.label_content.split('\n')[0].split(': ')[1];
    } else {
        console.error('scanned-result element not found');
    }
    
    const printButton = document.getElementById('print-button');
    if (printButton) {
        printButton.disabled = false;
    } else {
        console.error('print-button element not found');
    }

    if (stage === 'second-stage') {
        updateSecondStageInfo(data);
    }
}

function updateSecondStageInfo(data) {
    const elements = ['serial-number', 'imei-number', 'unique-number'];
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = data[id.replace('-', '_')] || 'N/A';
        } else {
            console.error(`${id} element not found`);
        }
    });
}

function showLabelPreview(labelPdfBase64) {
    console.log('Showing label preview');
    const previewContainer = document.getElementById('preview-container');
    previewContainer.innerHTML = '';

    const embedElement = document.createElement('embed');
    embedElement.src = labelPdfBase64;
    embedElement.type = 'application/pdf';
    embedElement.width = '100%';
    embedElement.height = '400px';

    previewContainer.appendChild(embedElement);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded');
    const stage = document.body.dataset.stage;
    if (stage) {
        console.log(`Initializing ${stage}`);
        initBarcodeInput(stage);
    } else {
        console.error('No stage found in body dataset');
    }
});
