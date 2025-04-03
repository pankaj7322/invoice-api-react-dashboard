from flask import Blueprint, request, jsonify
from google import genai
import re
from datetime import datetime
import json
import sqlite3
import fitz  # PyMuPDF for PDF text extraction

client = genai.Client(api_key="AIzaSyBI8SCeFG6Mq6xQX92m_h7HXZPbBZBa8m0")

invoice_bp = Blueprint('invoice_bp', __name__)

@invoice_bp.route('/extract_invoice', methods=['POST'])
def extract_invoice():
    """Route to handle invoice file extraction using Gemini."""
    file = request.files.get('invoice_file')

    print("file", file)

    if not file:
        return jsonify({"error": "No File uploaded"}), 400

    # Extract text from PDF file
    file_contents = extract_text_from_pdf(file)

    if not file_contents:
        return jsonify({"error": "Failed to extract text from PDF"}), 500

    # Call the Gemini API with the extracted text
    cleaned_data = extract_invoice_data_from_gemini(file_contents)

    if cleaned_data is None:
        return jsonify({'error': "Error extracting invoice data"}), 500

    # Return the extracted invoice data as response (no database part yet)
    return jsonify(cleaned_data), 200

def extract_text_from_pdf(file):
    """Extract text from the uploaded PDF file."""
    try:
        # Open the file using PyMuPDF (fitz)
        doc = fitz.open(stream=file.read(), filetype="pdf")

        # Extract text from each page
        text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()

        return text.strip()  # Return the extracted text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_invoice_data_from_gemini(file):
    """Call the Gemini API to extract invoice data from extracted text."""
    try:

        # file_contents = file.read().decode('utf-8')

        prompt = f"""
        Extract the following invoice details from the text:
        - Invoice Number
        - Invoice date
        - Amount 
        - Due Date

        please return the extracted data in the following format:
        {{
            "invoice_number": "<Invoice Number>",
            "invoice_date": "<Invoice Data in YYYY-MM-DD format>",
            "amount": <Amount as a float (remove the dollar sign)>,
            "due data": "<Due Date in YYYY-MM-DD format>
        }}

        Ensure the values are in the proper format. If any field is missing, use "NOT Available" as the value for that field.
        """

        # Call the Gemini API to extract invoice data from the file contents
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents= prompt + file
        )

              
        data = response.text

        cleaned_data = clean_invoice_data(data)
        print("Invoice_data", cleaned_data)
        return cleaned_data
    
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return None


def clean_invoice_data(json_string):

    print("json_string", json_string)
    data = json_string.strip('`json')
    print("new_data", data)

    json_data = json.loads(data)

    cleaned_data = {
                "invoice_number": clean_invoice_number(json_data.get("invoice_number")),
                "invoice_date": clean_date(json_data.get("invoice_date")),
                "amount": clean_amount(json_data.get("amount")),
                "due_date": clean_date(json_data.get("due data"))
            }
    
    try:
        conn = sqlite3.connect('invoice.db')
        cursor = conn.cursor()

        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT,
                invoice_date TEXT,
                amount REAL,
                due_date TEXT
            )
        ''')

        # Insert the cleaned invoice data into the database
        cursor.execute('''
            INSERT INTO invoices (invoice_number, invoice_date, amount, due_date)
            VALUES (?, ?, ?, ?)
        ''', (cleaned_data["invoice_number"], cleaned_data["invoice_date"], cleaned_data["amount"], cleaned_data["due_date"]))

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        return f"Invoice {cleaned_data['invoice_number']} saved successfully."
    
    except Exception as e:
        if conn:
            conn.rollback()  # Rollback in case of an error
            conn.close()
        return f"Error saving invoice: {str(e)}"





# Clean invoice number (if "NOT Available", return default value)
def clean_invoice_number(value):
    if value == "NOT Available" or value == "Not Found":
        return "Not Available"
    return value.strip() if value else "Not Available"

# Clean date (ensure proper date format)
def clean_date(value):
    print("date", value)
    if value == "NOT Available":
        return None  # We can choose to store NULL if the date is not available
    
    try:
        # Convert string to date (YYYY-MM-DD format)
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None  # Return None if the date format is invalid

# Clean amount (remove '$' and ',' and convert to float)
def clean_amount(value):
    if value == "NOT Available" or value is None:
        return 0.0
    
    try:
        # Remove any non-numeric characters (e.g., dollar sign)
        return float(str(value).replace('$', '').replace(',', '').strip())
    except ValueError:
        return 0.0
    

@invoice_bp.route('/get_invoices', methods = ['GET'])
def get_invoices():
    """Route to fetch all invoices from the database"""
    try:
        conn = sqlite3.connect('invoice.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM invoices')
        invoices = cursor.fetchall()

        conn.close()

        invoice_list = []
        for invoice in invoices:
            invoice_data = {
                "id": invoice[0],
                "invoice_number": invoice[1],
                "invoice_date": invoice[2],
                "amount": invoice[3],
                "due_date": invoice[4]
            }
            invoice_list.append(invoice_data)

        return jsonify(invoice_list), 200
    except Exception as e:
        print(f"Error fetching invoices from database: {e}")
        return jsonify({"error": "Failed to retrieve invoices"}), 500

