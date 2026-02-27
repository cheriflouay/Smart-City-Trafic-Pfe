# src/api/gov_reports.py
from fpdf import FPDF
import pandas as pd
from datetime import datetime
from src.database.db import get_connection
import os

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Capgemini Smart City - Intersection Analytics', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_monthly_report():
    conn = get_connection()
    df_vio = pd.read_sql_query("SELECT violation_type, fine_amount FROM violations", conn)
    df_inc = pd.read_sql_query("SELECT incident_type FROM incidents", conn)
    conn.close()

    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(0, 10, f"Report Generated: {datetime.now().strftime('%Y-%m-%d')}", 0, 1)
    pdf.ln(10)

    # Financials
    total_rev = df_vio['fine_amount'].sum() if not df_vio.empty else 0
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"1. Financial Summary", 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Total Projected Revenue: {total_rev} TND", 0, 1)
    pdf.cell(0, 10, f"Total Violations Issued: {len(df_vio)}", 0, 1)
    pdf.ln(5)

    # Safety
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"2. Safety & Hazards", 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Total Physical Incidents Detected: {len(df_inc)}", 0, 1)

    os.makedirs("exports", exist_ok=True)
    filename = f"exports/Gov_Report_{datetime.now().strftime('%Y%m')}.pdf"
    pdf.output(filename, 'F')
    return filename

if __name__ == "__main__":
    filepath = generate_monthly_report()
    print(f"📄 Report saved to {filepath}")