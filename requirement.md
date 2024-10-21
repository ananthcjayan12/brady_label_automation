# Product Requirements Document: Two-Stage Barcode Scanning and Printing System

## 1. Project Overview
This project aims to create a modern, user-friendly web application for a two-stage barcode scanning and printing system. The application will be built using Django templates for the frontend, styled with Bootstrap and custom CSS for a sleek and responsive interface.

---

## 2. User Interface Requirements
- **UI Design**: Create a modern, minimalist design using Django templates.
- **Responsiveness**: Implement a responsive layout with Bootstrap for seamless performance on various screen sizes.
- **Color Scheme & Icons**: Use a clean, consistent color palette with intuitive icons.
- **Base Template**: Develop a reusable base template (`base.html`) for consistent layout across pages.
- **Custom CSS**: Utilize custom CSS for unique styling and subtle animations.

---

## 3. Main Dashboard
- **Main Options**: Display two prominent options on the dashboard:
  1. **First Stage**
  2. **Second Stage**

---

## 4. First Stage Process
1. When the user selects **"First Stage"**:
2. **Activate Camera/Barcode Scanner**: Trigger the device’s camera or connect to a scanner.
3. **Scan and Read Barcode**: Capture barcode data from the scanned item.
4. **Duplicate Barcode Data**: Create a duplicate of the scanned barcode.
5. **Generate Label**: Produce a label with the duplicated barcode.
6. **Send to Printer**: Print the label using the connected printer.

---

## 5. Second Stage Process
1. When the user selects **"Second Stage"**:
2. **Activate Camera/Barcode Scanner**: Activate the camera or scanner to scan the item.
3. **Scan and Extract Data**: Retrieve the barcode data and extract the **serial number**.
4. **Excel Sheet Lookup**:
   - Search the corresponding **IMEI number** and **unique number** from a specified Excel file located on the server.
5. **Generate Label**: Create a label containing:
   - Original barcode information
   - Extracted serial number
   - Corresponding IMEI number
   - Corresponding unique number
6. **Send to Printer**: Print the label using the connected printer.
7. **Update Excel Sheet**: Mark the item as printed in the Excel sheet.

---

## 6. Excel Sheet Integration
- **Secure Access**: Enable secure access to the Excel file on the server.
- **Efficient Lookup**: Ensure fast and accurate searches by serial number.
- **Error Handling**: Implement error messages when data is not found.

---

## 7. Admin Dashboard
- **Overview**: Provide an overview of both **First Stage** and **Second Stage** operations.
- **Statistics**: Display statistics on the number of items processed.
- **Logs**: Allow viewing and exporting of operational logs.
- **User Management**: Enable account management and permission control.
- **Excel Management**: Provide functionality to update or modify Excel data.

---

## 8. Security and Data Management
- **Authentication & Authorization**: Use Django’s authentication system for secure access.
- **Secure Data Handling**: Protect sensitive information (e.g., IMEI numbers).
- **Data Backups**: Implement regular backups for data safety.
- **Audit Trails**: Provide a detailed audit trail of all operations.

---

## 9. Technical Requirements
- **Framework**: Develop the system using the Django framework.
- **Frontend**: Use Django templates for view rendering.
- **Bootstrap**: Apply Bootstrap 5 for responsive design.
- **CSS Styling**: Include custom CSS for additional animations and styling.
- **Django Forms**: Use Django Forms for input validation.
- **Class-Based Views**: Organize code using Django’s Class-Based Views.
- **Barcode Scanner & Printer**: Ensure compatibility with common barcode scanners and printers.
- **Database Operations**: Utilize Django’s ORM for efficient database management.

---

## 10. Frontend Structure
- **Base Template**: Develop a `base.html` template for shared page elements.
- **Template Inheritance**: Extend `base.html` for other pages.
- **Static Files Organization**: Store CSS, JavaScript, and images in structured directories.
- **Mobile-First Design**: Implement CSS with a mobile-first approach.

---

## 11. JavaScript Usage
- **Lightweight JavaScript**: Use vanilla JavaScript or minimal jQuery for dynamic interactions.
- **AJAX Calls**: Utilize the Fetch API or jQuery to perform AJAX calls for seamless updates.



### Developer Instructions
1. **Setup and Configuration**:
   - Install Django and set up the project environment.
   - Configure Bootstrap and link custom CSS.
   - Create and structure the `base.html` template.

2. **Implement First Stage**:
   - Integrate barcode scanning functionality using camera/scanner.
   - Create a view for generating and printing barcode labels.

3. **Implement Second Stage**:
   - Add logic to scan barcodes, extract serial numbers, and lookup Excel data.
   - Develop a label generation view that includes IMEI and unique numbers.
   - Ensure Excel sheet updates after printing.

4. **Admin Dashboard Development**:
   - Build views for st
