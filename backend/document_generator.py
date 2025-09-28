from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, HexColor
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
from typing import Dict, Any, List
import os
from io import BytesIO

# Adela Merchants brand colors (exact from letterhead analysis)
ADELA_YELLOW = HexColor('#FFEA00')  # Bright vibrant yellow from letterhead
ADELA_BLACK = HexColor('#000000')   # Pure black for curves
ADELA_LIGHT_YELLOW = HexColor('#FFF3A3')  # Light watermark yellow
ADELA_WHITE = HexColor('#FFFFFF')   # White background
ADELA_DARK_GRAY = HexColor('#333333')  # Dark text
ADELA_LIGHT_GRAY = HexColor('#F5F5F5')  # Light gray for backgrounds

class DocumentGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 20 * mm
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for Adela Merchants branding"""
        # Company header style
        if 'AdelaHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='AdelaHeader',
                fontSize=24,
                textColor=ADELA_BLACK,
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
    
    def draw_letterhead_header(self, canvas_obj, doc):
        """Draw the Adela Merchants letterhead header with curved bands"""
        canvas_obj.saveState()
        
        # Header yellow band (curved, extends from left to 85% width)
        path = canvas_obj.beginPath()
        path.moveTo(0, self.page_height - 80)
        path.curveTo(100, self.page_height - 60, 
                    self.page_width * 0.6, self.page_height - 70,
                    self.page_width * 0.85, self.page_height - 50)
        path.lineTo(self.page_width * 0.85, self.page_height)
        path.lineTo(0, self.page_height)
        path.closePath()
        canvas_obj.setFillColor(ADELA_YELLOW)
        canvas_obj.drawPath(path, fill=1, stroke=0)
        
        # Header black curved band (inside yellow band)
        path = canvas_obj.beginPath()
        path.moveTo(self.page_width * 0.3, self.page_height - 75)
        path.curveTo(self.page_width * 0.4, self.page_height - 65,
                    self.page_width * 0.5, self.page_height - 68,
                    self.page_width * 0.65, self.page_height - 55)
        path.curveTo(self.page_width * 0.7, self.page_height - 70,
                    self.page_width * 0.45, self.page_height - 80,
                    self.page_width * 0.3, self.page_height - 85)
        path.closePath()
        canvas_obj.setFillColor(ADELA_BLACK)
        canvas_obj.drawPath(path, fill=1, stroke=0)
        
        # Company name "ADELA MERCHANTS"
        canvas_obj.setFillColor(ADELA_BLACK)
        canvas_obj.setFont("Helvetica-Bold", 18)
        canvas_obj.drawString(40, self.page_height - 45, "ADELA MERCHANTS")
        
        # ABN in top right
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawRightString(self.page_width - 40, self.page_height - 35, "ABN - 6268 104 6435")
        
        # Large watermark monogram (light yellow, centered)
        canvas_obj.setFillColor(ADELA_LIGHT_YELLOW)
        canvas_obj.setFont("Helvetica-Bold", 120)
        canvas_obj.drawCentredText(self.page_width/2, self.page_height * 0.6, "AM")
        
        canvas_obj.restoreState()
    
    def draw_letterhead_footer(self, canvas_obj, doc):
        """Draw the Adela Merchants letterhead footer with contact info"""
        canvas_obj.saveState()
        
        # Footer yellow band (mirrors header)
        path = canvas_obj.beginPath()
        path.moveTo(0, 80)
        path.curveTo(100, 60, 
                    self.page_width * 0.6, 70,
                    self.page_width * 0.85, 50)
        path.lineTo(self.page_width * 0.85, 0)
        path.lineTo(0, 0)
        path.closePath()
        canvas_obj.setFillColor(ADELA_YELLOW)
        canvas_obj.drawPath(path, fill=1, stroke=0)
        
        # Footer black curved band
        path = canvas_obj.beginPath()
        path.moveTo(self.page_width * 0.1, 75)
        path.curveTo(self.page_width * 0.2, 65,
                    self.page_width * 0.3, 68,
                    self.page_width * 0.45, 55)
        path.curveTo(self.page_width * 0.5, 70,
                    self.page_width * 0.25, 80,
                    self.page_width * 0.1, 85)
        path.closePath()
        canvas_obj.setFillColor(ADELA_BLACK)
        canvas_obj.drawPath(path, fill=1, stroke=0)
        
        # Contact information (bottom left)
        canvas_obj.setFillColor(ADELA_BLACK)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(40, 45, "📧 info@adelamerchants.com.au")
        canvas_obj.drawString(40, 30, "🌐 www.adelamerchants.com.au")
        canvas_obj.drawString(40, 15, "📍 123 Business St, Melbourne VIC 3000")
        
        canvas_obj.restoreState()
        
        # Document title style
        if 'DocumentTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='DocumentTitle',
                fontSize=18,
                textColor=ADELA_BLACK,
                spaceAfter=15,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        # Section header style
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                fontSize=12,
                textColor=ADELA_BLACK,
                spaceAfter=8,
                fontName='Helvetica-Bold',
                backColor=ADELA_LIGHT_GRAY
            ))
        
        # Body text style
        if 'AdelaBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='AdelaBodyText',
                fontSize=10,
                textColor=ADELA_BLACK,
                spaceAfter=6,
                fontName='Helvetica'
            ))
    
    def _draw_header(self, canvas_obj, doc_title: str):
        """Draw Adela Merchants letterhead header with curved elements"""
        canvas_obj.saveState()
        
        # Draw top curved element (simplified version)
        canvas_obj.setFillColor(ADELA_YELLOW)
        canvas_obj.roundRect(self.margin, self.page_height - 40*mm, 
                           self.page_width - 2*self.margin, 25*mm, 10)
        
        # Company name
        canvas_obj.setFillColor(ADELA_BLACK)
        canvas_obj.setFont('Helvetica-Bold', 18)
        canvas_obj.drawCentredString(self.page_width/2, self.page_height - 25*mm, 
                                 "ADELA MERCHANTS")
        
        # ABN (placeholder - should be from your actual ABN)
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.drawRightString(self.page_width - self.margin - 10*mm, 
                                 self.page_height - 15*mm, "ABN: XX XXX XXX XXX")
        
        # Document title
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.drawCentredString(self.page_width/2, self.page_height - 50*mm, doc_title)
        
        canvas_obj.restoreState()
    
    def _draw_footer(self, canvas_obj):
        """Draw footer with contact information"""
        canvas_obj.saveState()
        
        # Bottom curved element
        canvas_obj.setFillColor(ADELA_YELLOW)
        canvas_obj.roundRect(self.margin, 15*mm, 
                           self.page_width - 2*self.margin, 20*mm, 10)
        
        # Contact information
        canvas_obj.setFillColor(ADELA_BLACK)
        canvas_obj.setFont('Helvetica', 9)
        
        # Email, Website, Address (from letterhead format)
        y_pos = 25*mm
        canvas_obj.drawString(self.margin + 10*mm, y_pos, 
                            "✉ info@adelamerchants.com.au")
        canvas_obj.drawString(self.margin + 80*mm, y_pos,
                            "🌐 www.adelamerchants.com.au")
        canvas_obj.drawString(self.margin + 160*mm, y_pos,
                            "📍 Your Business Address")
        
        canvas_obj.restoreState()
    
    def generate_order_acknowledgment(self, order_data: Dict[str, Any]) -> bytes:
        """Generate order acknowledgment PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=self.margin, leftMargin=self.margin,
                              topMargin=60*mm, bottomMargin=40*mm)
        
        story = []
        
        # Calculate delivery date based on client lead time
        lead_time_days = order_data.get('client_lead_time_days', 7)
        from datetime import datetime, timedelta
        delivery_date = datetime.now() + timedelta(days=lead_time_days)
        
        # Order details table
        order_data_table = [
            ['Order Number:', order_data.get('order_number', 'N/A')],
            ['Invoice Number:', order_data.get('invoice_number', 'TBD')],
            ['Date:', datetime.now().strftime('%d/%m/%Y')],
            ['Due Date:', order_data.get('due_date', 'N/A')],
            ['Estimated Delivery:', delivery_date.strftime('%d/%m/%Y')],
            ['Lead Time:', f"{lead_time_days} business days"]
        ]
        
        order_table = Table(order_data_table, colWidths=[40*mm, 60*mm])
        order_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(order_table)
        story.append(Spacer(1, 20))
        
        # Customer details
        story.append(Paragraph("Customer Details", self.styles['SectionHeader']))
        customer_info = f"""
        <b>{order_data.get('client_name', 'N/A')}</b><br/>
        {order_data.get('client_address', 'N/A')}<br/>
        Email: {order_data.get('client_email', 'N/A')}<br/>
        Phone: {order_data.get('client_phone', 'N/A')}
        """
        story.append(Paragraph(customer_info, self.styles['AdelaBodyText']))
        story.append(Spacer(1, 15))
        
        # Order items
        story.append(Paragraph("Order Items", self.styles['SectionHeader']))
        
        # Items table header
        items_data = [['Product', 'Quantity', 'Unit Price', 'Total']]
        
        # Add items
        for item in order_data.get('items', []):
            items_data.append([
                item.get('product_name', 'N/A'),
                str(item.get('quantity', 0)),
                f"${item.get('unit_price', 0):.2f}",
                f"${item.get('total_price', 0):.2f}"
            ])
        
        # Add totals
        items_data.extend([
            ['', '', 'Subtotal:', f"${order_data.get('subtotal', 0):.2f}"],
            ['', '', 'GST (10%):', f"${order_data.get('gst', 0):.2f}"],
            ['', '', 'Total:', f"${order_data.get('total_amount', 0):.2f}"]
        ])
        
        items_table = Table(items_data, colWidths=[60*mm, 30*mm, 40*mm, 40*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ADELA_LIGHT_GRAY),
            ('TEXTCOLOR', (0, 0), (-1, 0), ADELA_BLACK),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Product names left-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, ADELA_BLACK),
            # Highlight totals
            ('BACKGROUND', (2, -3), (-1, -1), ADELA_LIGHT_GRAY),
            ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Payment terms and delivery information
        story.append(Paragraph("Terms & Conditions", self.styles['SectionHeader']))
        
        payment_terms = order_data.get('client_payment_terms', 'Net 30 days')
        terms_info = f"""
        <b>Payment Terms:</b> {payment_terms}<br/>
        <b>Delivery Terms:</b> Delivery will commence approximately {lead_time_days} business days from order confirmation.<br/>
        <b>Special Instructions:</b> {order_data.get('delivery_instructions', 'Standard delivery terms apply.')}<br/>
        """
        story.append(Paragraph(terms_info, self.styles['AdelaBodyText']))
        story.append(Spacer(1, 10))
        
        # Bank details for payment
        if order_data.get('bank_details'):
            story.append(Paragraph("Payment Details", self.styles['SectionHeader']))
            bank_info = order_data['bank_details']
            payment_info = f"""
            <b>Bank:</b> {bank_info.get('bank_name', 'N/A')}<br/>
            <b>Account Name:</b> {bank_info.get('account_name', 'N/A')}<br/>
            <b>BSB:</b> {bank_info.get('bsb', 'N/A')}<br/>
            <b>Account Number:</b> {bank_info.get('account_number', 'N/A')}<br/>
            <b>Reference:</b> {order_data.get('order_number', 'N/A')}
            """
            story.append(Paragraph(payment_info, self.styles['AdelaBodyText']))
        
        # Build PDF with custom header/footer
        def add_header_footer(canvas_obj, doc):
            self._draw_header(canvas_obj, "ORDER ACKNOWLEDGMENT")
            self._draw_footer(canvas_obj)
        
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_job_card(self, job_data: Dict[str, Any]) -> bytes:
        """Generate printable job card PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=self.margin, leftMargin=self.margin,
                              topMargin=60*mm, bottomMargin=40*mm)
        
        story = []
        
        # Job card header
        job_header_data = [
            ['Job Number:', job_data.get('order_number', 'N/A')],
            ['Client:', job_data.get('client_name', 'N/A')],
            ['Due Date:', job_data.get('due_date', 'N/A')],
            ['Priority:', job_data.get('priority', 'Normal')]
        ]
        
        job_header_table = Table(job_header_data, colWidths=[40*mm, 80*mm])
        job_header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(job_header_table)
        story.append(Spacer(1, 20))
        
        # Production stages checklist
        story.append(Paragraph("Production Stages", self.styles['SectionHeader']))
        
        stages = [
            'Order Entered', 'Pending Material', 'Paper Slitting', 
            'Winding', 'Finishing', 'Delivery', 'Invoicing'
        ]
        
        for stage in stages:
            current_stage = job_data.get('current_stage', '').replace('_', ' ').title()
            checkbox = "☑" if stage == current_stage else "☐"
            story.append(Paragraph(f"{checkbox} {stage}", self.styles['AdelaBodyText']))
        
        story.append(Spacer(1, 20))
        
        # Job specifications
        if job_data.get('specifications'):
            story.append(Paragraph("Job Specifications", self.styles['SectionHeader']))
            specs = job_data['specifications']
            spec_text = f"""
            <b>Material Type:</b> {specs.get('material_type', 'N/A')}<br/>
            <b>Dimensions:</b> {specs.get('dimensions', 'N/A')}<br/>
            <b>Weight:</b> {specs.get('weight', 'N/A')}<br/>
            <b>Color:</b> {specs.get('color', 'N/A')}<br/>
            <b>Finishing:</b> {specs.get('finishing_requirements', 'N/A')}<br/>
            <b>Quality Standards:</b> {specs.get('quality_standards', 'N/A')}<br/>
            <b>Special Instructions:</b> {specs.get('special_instructions', 'N/A')}
            """
            story.append(Paragraph(spec_text, self.styles['AdelaBodyText']))
            story.append(Spacer(1, 15))
        
        # Notes section
        story.append(Paragraph("Production Notes", self.styles['SectionHeader']))
        story.append(Spacer(1, 40))  # Space for handwritten notes
        
        # Quality control section
        story.append(Paragraph("Quality Control Checkpoints", self.styles['SectionHeader']))
        qc_checkpoints = [
            "Material inspection completed: ☐",
            "Dimensions verified: ☐",
            "Finishing quality approved: ☐",
            "Final inspection passed: ☐"
        ]
        
        for checkpoint in qc_checkpoints:
            story.append(Paragraph(checkpoint, self.styles['AdelaBodyText']))
        
        # Build PDF
        def add_header_footer(canvas_obj, doc):
            self._draw_header(canvas_obj, "JOB CARD")
            self._draw_footer(canvas_obj)
        
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_packing_list(self, order_data: Dict[str, Any]) -> bytes:
        """Generate packing list PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=self.margin, leftMargin=self.margin,
                              topMargin=60*mm, bottomMargin=40*mm)
        
        story = []
        
        # Packing list header
        packing_header = [
            ['Order Number:', order_data.get('order_number', 'N/A')],
            ['Customer:', order_data.get('client_name', 'N/A')],
            ['Ship Date:', datetime.now().strftime('%d/%m/%Y')],
            ['Delivery Address:', order_data.get('delivery_address', 'N/A')]
        ]
        
        header_table = Table(packing_header, colWidths=[40*mm, 80*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 25))
        
        # Items to pack
        story.append(Paragraph("Items to Pack", self.styles['SectionHeader']))
        
        items_data = [['Item', 'Quantity', 'Packed', 'Notes']]
        
        for item in order_data.get('items', []):
            items_data.append([
                item.get('product_name', 'N/A'),
                str(item.get('quantity', 0)),
                '☐',  # Checkbox for packed
                ''    # Space for notes
            ])
        
        items_table = Table(items_data, colWidths=[60*mm, 30*mm, 25*mm, 55*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ADELA_LIGHT_GRAY),
            ('TEXTCOLOR', (0, 0), (-1, 0), ADELA_BLACK),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, ADELA_BLACK),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 30))
        
        # Delivery instructions
        if order_data.get('delivery_instructions'):
            story.append(Paragraph("Delivery Instructions", self.styles['SectionHeader']))
            story.append(Paragraph(order_data['delivery_instructions'], self.styles['AdelaBodyText']))
            story.append(Spacer(1, 20))
        
        # Signature section
        story.append(Paragraph("Packed by: _________________ Date: _______", self.styles['AdelaBodyText']))
        story.append(Spacer(1, 15))
        story.append(Paragraph("Checked by: _________________ Date: _______", self.styles['AdelaBodyText']))
        
        # Build PDF
        def add_header_footer(canvas_obj, doc):
            self._draw_header(canvas_obj, "PACKING LIST")
            self._draw_footer(canvas_obj)
        
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_invoice(self, invoice_data: Dict[str, Any]) -> bytes:
        """Generate invoice PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=self.margin, leftMargin=self.margin,
                              topMargin=60*mm, bottomMargin=40*mm)
        
        story = []
        
        # Invoice header
        invoice_header = [
            ['Invoice Number:', invoice_data.get('invoice_number', 'N/A')],
            ['Order Number:', invoice_data.get('order_number', 'N/A')],
            ['Invoice Date:', datetime.now().strftime('%d/%m/%Y')],
            ['Due Date:', invoice_data.get('payment_due_date', 'N/A')]
        ]
        
        header_table = Table(invoice_header, colWidths=[40*mm, 60*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Bill to section
        story.append(Paragraph("Bill To:", self.styles['SectionHeader']))
        bill_to_info = f"""
        <b>{invoice_data.get('client_name', 'N/A')}</b><br/>
        {invoice_data.get('client_address', 'N/A')}<br/>
        ABN: {invoice_data.get('client_abn', 'N/A')}
        """
        story.append(Paragraph(bill_to_info, self.styles['AdelaBodyText']))
        story.append(Spacer(1, 20))
        
        # Invoice items
        items_data = [['Description', 'Quantity', 'Unit Price', 'Total']]
        
        for item in invoice_data.get('items', []):
            items_data.append([
                item.get('product_name', 'N/A'),
                str(item.get('quantity', 0)),
                f"${item.get('unit_price', 0):.2f}",
                f"${item.get('total_price', 0):.2f}"
            ])
        
        # Add totals
        items_data.extend([
            ['', '', '', ''],  # Blank row
            ['', '', 'Subtotal:', f"${invoice_data.get('subtotal', 0):.2f}"],
            ['', '', 'GST (10%):', f"${invoice_data.get('gst', 0):.2f}"],
            ['', '', 'TOTAL DUE:', f"${invoice_data.get('total_amount', 0):.2f}"]
        ])
        
        items_table = Table(items_data, colWidths=[70*mm, 30*mm, 35*mm, 35*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ADELA_LIGHT_GRAY),
            ('TEXTCOLOR', (0, 0), (-1, 0), ADELA_BLACK),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -4), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -4), 1, ADELA_BLACK),
            # Totals styling
            ('FONTNAME', (2, -3), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (2, -1), (-1, -1), ADELA_YELLOW),
            ('FONTSIZE', (2, -1), (-1, -1), 12),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 30))
        
        # Payment terms
        story.append(Paragraph("Payment Terms: Net 30 days", self.styles['AdelaBodyText']))
        story.append(Paragraph("Thank you for your business!", self.styles['AdelaBodyText']))
        
        # Build PDF
        def add_header_footer(canvas_obj, doc):
            self._draw_header(canvas_obj, "INVOICE")
            self._draw_footer(canvas_obj)
        
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()