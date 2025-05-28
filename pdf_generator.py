# pdf_generator.py
"""
PDFExportManager handles invoice rendering to PDF using ReportLab.
"""
import os
from typing import Tuple, Optional
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import HexColor, black, gray, lightgrey
from reportlab.lib.units import inch, cm
from decimal import Decimal

from models import Invoice as BusinessInvoice  # Business logic model
from utils import format_currency, sanitize_filename, parse_date_string
from config.constants import (
    APP_NAME, PDF_PAGE_SIZE, PDF_FONT_NAME, PDF_FONT_NAME_BOLD,
    PDF_FONT_SIZE_NORMAL, PDF_FONT_SIZE_LARGE, PDF_FONT_SIZE_SMALL,
    CURRENCY_SYMBOL
)
from config.config_manager import load_config

# --- ReportLab Styles ---
STYLES = getSampleStyleSheet()
STYLES.add(
    ParagraphStyle(name='Normal_Right', alignment=TA_RIGHT, fontName=PDF_FONT_NAME, fontSize=PDF_FONT_SIZE_NORMAL))
STYLES.add(
    ParagraphStyle(name='Normal_Center', alignment=TA_CENTER, fontName=PDF_FONT_NAME, fontSize=PDF_FONT_SIZE_NORMAL))
STYLES.add(ParagraphStyle(name='Body_Bold', fontName=PDF_FONT_NAME_BOLD, fontSize=PDF_FONT_SIZE_NORMAL))
STYLES.add(
    ParagraphStyle(name='Header_Main', alignment=TA_LEFT, fontName=PDF_FONT_NAME_BOLD, fontSize=PDF_FONT_SIZE_LARGE + 4,
                   leading=18))
STYLES.add(ParagraphStyle(name='Header_Sub', alignment=TA_RIGHT, fontName=PDF_FONT_NAME, fontSize=PDF_FONT_SIZE_NORMAL,
                          textColor=gray))
STYLES.add(ParagraphStyle(name='Footer', alignment=TA_CENTER, fontName=PDF_FONT_NAME, fontSize=PDF_FONT_SIZE_SMALL,
                          textColor=gray))
STYLES.add(
    ParagraphStyle(name='Table_Header', fontName=PDF_FONT_NAME_BOLD, fontSize=PDF_FONT_SIZE_NORMAL, alignment=TA_CENTER,
                   textColor=black, backColor=lightgrey))
STYLES.add(
    ParagraphStyle(name='Table_Cell_Right', fontName=PDF_FONT_NAME, fontSize=PDF_FONT_SIZE_NORMAL, alignment=TA_RIGHT))
STYLES.add(
    ParagraphStyle(name='Total_Label', fontName=PDF_FONT_NAME_BOLD, fontSize=PDF_FONT_SIZE_NORMAL, alignment=TA_RIGHT))
STYLES.add(
    ParagraphStyle(name='Total_Value', fontName=PDF_FONT_NAME_BOLD, fontSize=PDF_FONT_SIZE_LARGE, alignment=TA_RIGHT))


class PDFExportManager:
    """Handles the creation and exporting of invoices to PDF format."""

    def __init__(self):
        self.app_config = load_config()
        self.company_details = self.app_config.get("company_details", {  # Add to settings.json
            "name": "Your Company Name",
            "address_line1": "123 Main Street",
            "address_line2": "City, State, ZIP",
            "contact": "Phone: (555) 123-4567 | Email: contact@yourcompany.com",
            "logo_path": None  # Optional path to company logo image
        })
        self.page_size = A4 if PDF_PAGE_SIZE.upper() == "A4" else letter

    def _add_page_number(self, canvas, doc):
        """Adds page number to each page."""
        canvas.saveState()
        canvas.setFont(PDF_FONT_NAME, PDF_FONT_SIZE_SMALL)
        page_num_text = f"Page {doc.page}"
        canvas.drawRightString(self.page_size[0] - 1 * cm, 1 * cm, page_num_text)
        canvas.restoreState()

    def export_to_pdf(self, invoice_data: BusinessInvoice, filename: str) -> Tuple[bool, str]:
        """
        Exports the given invoice data to a PDF file.
        Returns (success_status, message_or_filepath).
        """
        try:
            doc = SimpleDocTemplate(filename, pagesize=self.page_size,
                                    leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                                    topMargin=1.5 * cm, bottomMargin=2 * cm,  # Increased bottom margin for page number
                                    title=f"Invoice {invoice_data.invoice_number}",
                                    author=self.company_details.get("name", APP_NAME))

            story = []

            # 1. Header (Company Logo & Details, Invoice Title)
            # Placeholder for logo
            # if self.company_details.get("logo_path") and os.path.exists(self.company_details["logo_path"]):
            #     logo = Image(self.company_details["logo_path"], width=2*inch, height=0.75*inch) # Adjust size
            #     logo.hAlign = 'LEFT'
            #     story.append(logo)
            #     story.append(Spacer(1, 0.25*inch))

            company_header_data = [
                [Paragraph(self.company_details.get("name", "Your Company"), STYLES['Header_Main']),
                 Paragraph("INVOICE", STYLES['Header_Sub'])],
                [Paragraph(self.company_details.get("address_line1", ""), STYLES['Normal']), ""],
                [Paragraph(self.company_details.get("address_line2", ""), STYLES['Normal']), ""],
                [Paragraph(self.company_details.get("contact", ""), STYLES['Normal']), ""],
            ]
            company_table = Table(company_header_data, colWidths=[doc.width * 0.65, doc.width * 0.35])
            company_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('SPAN', (0, 0), (0, 3)),  # Company details span multiple rows effectively
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),  # Invoice title
            ]))
            story.append(company_table)
            story.append(Spacer(1, 0.5 * inch))

            # 2. Bill To and Invoice Info
            invoice_date_str = invoice_data.invoice_date
            if parse_date_string(invoice_data.invoice_date):  # Format if valid
                invoice_date_str = parse_date_string(invoice_data.invoice_date).strftime("%B %d, %Y")

            bill_to_info_data = [
                [Paragraph("<b>BILL TO:</b>", STYLES['Normal']), "",
                 Paragraph("<b>INVOICE #:</b>", STYLES['Normal_Right']),
                 Paragraph(invoice_data.invoice_number, STYLES['Normal'])],
                [Paragraph(invoice_data.customer_name, STYLES['Normal']), "",
                 Paragraph("<b>DATE:</b>", STYLES['Normal_Right']), Paragraph(invoice_date_str, STYLES['Normal'])],
                [Paragraph(invoice_data.customer_address.split('\n')[0] if invoice_data.customer_address else "",
                           STYLES['Normal']), "", "", ""],
            ]
            # Add more address lines if present
            if invoice_data.customer_address and '\n' in invoice_data.customer_address:
                for line in invoice_data.customer_address.split('\n')[1:]:
                    bill_to_info_data.append([Paragraph(line, STYLES['Normal']), "", "", ""])

            bill_to_table = Table(bill_to_info_data,
                                  colWidths=[doc.width * 0.5, doc.width * 0.1, doc.width * 0.2, doc.width * 0.2])
            bill_to_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Labels right aligned
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),  # Values left aligned
                ('SPAN', (0, 1), (0, len(bill_to_info_data) - 1)),  # Customer name and address span
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(bill_to_table)
            story.append(Spacer(1, 0.5 * inch))

            # 3. Line Items Table
            line_items_header = [
                Paragraph("<b>#</b>", STYLES['Table_Header']),
                Paragraph("<b>DESCRIPTION</b>", STYLES['Table_Header']),
                Paragraph("<b>QTY</b>", STYLES['Table_Header']),
                Paragraph("<b>UNIT PRICE</b>", STYLES['Table_Header']),
                Paragraph("<b>SUBTOTAL</b>", STYLES['Table_Header'])
            ]
            line_items_data = [line_items_header]

            for item in invoice_data.line_items:
                row = [
                    Paragraph(str(item.number), STYLES['Normal_Center']),
                    Paragraph(item.description, STYLES['Normal']),
                    Paragraph(str(item.quantity), STYLES['Table_Cell_Right']),
                    Paragraph(format_currency(item.price, currency_symbol=CURRENCY_SYMBOL), STYLES['Table_Cell_Right']),
                    Paragraph(format_currency(item.subtotal, currency_symbol=CURRENCY_SYMBOL),
                              STYLES['Table_Cell_Right'])
                ]
                line_items_data.append(row)

            # Column widths: #, Description, Qty, Unit Price, Subtotal
            # Adjust first and last for padding, middle ones relative to content
            table_col_widths = [0.5 * inch, doc.width - 4.5 * inch, 0.8 * inch, 1.2 * inch, 1.5 * inch]

            items_table = Table(line_items_data, colWidths=table_col_widths, repeatRows=1)
            items_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, gray),
                ('BACKGROUND', (0, 0), (-1, 0), lightgrey),  # Header background
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Item numbers centered
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Numeric columns right aligned
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 0.2 * inch))

            # 4. Totals Section
            total_amount_formatted = format_currency(invoice_data.total_amount, currency_symbol=CURRENCY_SYMBOL)
            totals_data = [
                ["", Paragraph("<b>TOTAL:</b>", STYLES['Total_Label']),
                 Paragraph(total_amount_formatted, STYLES['Total_Value'])]
            ]
            # Sum column widths should match last two columns of items table
            totals_table = Table(totals_data, colWidths=[doc.width - (table_col_widths[-2] + table_col_widths[-1]),
                                                         table_col_widths[-2], table_col_widths[-1]])
            totals_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Remove padding if aligning with table above
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(totals_table)
            story.append(Spacer(1, 0.5 * inch))

            # 5. Notes / Terms (Optional)
            # story.append(Paragraph("<b>Notes:</b> Thank you for your business!", STYLES['Normal']))

            doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            return True, filename
        except Exception as e:
            import traceback
            return False, f"Failed to generate PDF: {e}\n{traceback.format_exc()}"

    def export_and_open(self, invoice_data: BusinessInvoice, filename: str) -> Tuple[bool, str]:
        """Exports to PDF and then tries to open it with the default system viewer."""
        # Your original main_window.py calls this method
        success, message_or_filepath = self.export_to_pdf(invoice_data, filename)
        if success:
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(message_or_filepath)
                elif os.name == 'posix':  # macOS, Linux
                    import subprocess
                    if sys.platform == "darwin":  # macOS
                        subprocess.call(('open', message_or_filepath))
                    else:  # Linux
                        subprocess.call(('xdg-open', message_or_filepath))
                return True, f"PDF '{filename}' generated and opened."
            except Exception as e:
                return True, f"PDF '{filename}' generated but failed to open automatically: {e}"
        return False, message_or_filepath