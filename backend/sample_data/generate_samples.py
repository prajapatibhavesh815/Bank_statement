"""
Sample Bank Statement PDF Generator.
Generates realistic multi-bank statements:
1. HDFC Bank (Text-based multi-page PDF)
2. State Bank of India (Text-based PDF)
3. ICICI Bank (Text-based PDF)
4. Scanned Bank Statement (Image-based PDF for OCR verification)
"""
import os
import io
import pypdfium2 as pdfium
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_hdfc_statement() -> str:
    """Generates a realistic multi-page HDFC Bank statement."""
    pdf_path = os.path.join(OUT_DIR, "hdfc_sample_statement.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()

    elements = []

    # Title & Header
    title_style = ParagraphStyle(
        'HDFCTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#002B49'),
        spaceAfter=6,
    )
    elements.append(Paragraph("HDFC BANK LIMITED", title_style))
    elements.append(Paragraph("Account Branch: KORAMANGALA BRANCH, BANGALORE - 560034", styles['Normal']))
    elements.append(Spacer(1, 10))

    # Account Metadata Table
    meta_data = [
        [Paragraph("<b>Customer Name:</b> RAJESH VERMA", styles['Normal']),
         Paragraph("<b>Account Number:</b> 50100234918234", styles['Normal'])],
        [Paragraph("<b>Address:</b> 402, PALM GROVE, 4TH BLOCK", styles['Normal']),
         Paragraph("<b>IFSC Code:</b> HDFC0000128", styles['Normal'])],
        [Paragraph("<b>Statement Period:</b> 01/08/2024 to 31/08/2024", styles['Normal']),
         Paragraph("<b>Account Type:</b> SAVINGS BANK ACCOUNT", styles['Normal'])],
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 15))

    # Transactions Table
    # HDFC Columns: Date | Narration | Chq./Ref.No. | Value Dt | Withdrawal Amt. | Deposit Amt. | Closing Balance
    headers = ["Date", "Narration", "Chq/Ref No", "Value Dt", "Withdrawal (Dr)", "Deposit (Cr)", "Closing Balance"]
    
    rows = [headers]
    txns = [
        ("01/08/2024", "ACH CR INFOSYS LIMITED MONTHLY SALARY PAYROLL", "SAL4829102", "01/08/2024", "", "95,000.00", "1,25,000.00"),
        ("02/08/2024", "ACH DR HDFC HOME LOAN EMI PRINCIPAL AND INTEREST", "EMI901283", "02/08/2024", "32,500.00", "", "92,500.00"),
        ("03/08/2024", "UPI/421092837192/ZOMATO LIMITED/zomato@icici/DR", "UPI4210928", "03/08/2024", "650.00", "", "91,850.00"),
        ("05/08/2024", "UPI/421598201928/BLINKIT COMMERCE/blinkit@icici/DR", "UPI4215982", "05/08/2024", "1,240.00", "", "90,610.00"),
        ("08/08/2024", "BILLDESK BESCOM ELECTRICITY BILL ONLINE PAYMENT", "BES892019", "08/08/2024", "2,450.00", "", "88,160.00"),
        ("10/08/2024", "POS 489201 SHELL PETROL PUMP KORAMANGALA BLR", "POS489201", "10/08/2024", "3,500.00", "", "84,660.00"),
        ("12/08/2024", "NETFLIX ENTERTAINMENT SERVICES MUMBAI RECURRING", "SUB901928", "12/08/2024", "649.00", "", "84,011.00"),
        ("15/08/2024", "UPI/422891029384/AMAZON PAY INDIA/amazon@apl/DR", "UPI4228910", "15/08/2024", "4,299.00", "", "79,712.00"),
        ("18/08/2024", "ACH DR ZERODHA BROKING LTD MONTHLY TRADING ACC", "ZER928371", "18/08/2024", "15,000.00", "", "64,712.00"),
        ("20/08/2024", "ATM WDL-NFS-HDFC ATM 100FT ROAD KORAMANGALA", "ATM482019", "20/08/2024", "5,000.00", "", "59,712.00"),
        ("22/08/2024", "POS APOLLO PHARMACY BANGALORE MEDICINES", "POS391029", "22/08/2024", "850.00", "", "58,862.00"),
        ("25/08/2024", "UPI/423891029381/SWIGGY/swiggy@hdfc/Food Order", "UPI4238910", "25/08/2024", "420.00", "", "58,442.00"),
        ("27/08/2024", "UPI/424091827364/CRED BBPS CC PAYMENT/cred@axis", "UPI4240918", "27/08/2024", "12,500.00", "", "45,942.00"),
        ("29/08/2024", "UPI/424291029384/RAHUL SHARMA/rahul@oksbi/P2P", "UPI4242910", "29/08/2024", "3,000.00", "", "42,942.00"),
        ("31/08/2024", "CONSOLIDATED SMS ALERT AND ANNUAL CARD CHARGES", "CHG001928", "31/08/2024", "177.00", "", "42,765.00"),
        ("31/08/2024", "INT.PD:01-08-2024 TO 31-08-2024 SAVINGS INT CR", "INT491029", "31/08/2024", "", "285.00", "43,050.00"),
    ]

    for d, nar, ref, val_dt, dr, cr, bal in txns:
        p_nar = Paragraph(nar, styles['Normal'])
        rows.append([d, p_nar, ref, val_dt, dr, cr, bal])

    t_txns = Table(rows, colWidths=[55, 175, 65, 55, 65, 65, 65])
    t_txns.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (3, -1), 'CENTER'),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_txns)
    doc.build(elements)
    return pdf_path


def generate_sbi_statement() -> str:
    """Generates a realistic SBI bank statement."""
    pdf_path = os.path.join(OUT_DIR, "sbi_sample_statement.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()

    elements = []
    title_style = ParagraphStyle(
        'SBITitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=6,
    )
    elements.append(Paragraph("STATE BANK OF INDIA", title_style))
    elements.append(Paragraph("Branch: SATELLITE ROAD, AHMEDABAD - 380015", styles['Normal']))
    elements.append(Spacer(1, 10))

    meta_data = [
        [Paragraph("<b>Account Name:</b> BHAVESH PATEL", styles['Normal']),
         Paragraph("<b>Account Number:</b> 38291029481", styles['Normal'])],
        [Paragraph("<b>IFS Code:</b> SBIN0001824", styles['Normal']),
         Paragraph("<b>MICR:</b> 380002041", styles['Normal'])],
        [Paragraph("<b>Period:</b> 01-Sep-2024 to 30-Sep-2024", styles['Normal']),
         Paragraph("<b>Balance:</b> ₹ 68,450.00", styles['Normal'])],
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#BFDBFE')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DBEAFE')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 15))

    # SBI Table: Txn Date | Value Date | Description | Ref No./Cheque No. | Debit | Credit | Balance
    headers = ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit", "Balance"]
    rows = [headers]

    sbi_txns = [
        ("01-Sep-2024", "01-Sep-2024", "BY CLG SALARY CREDIT TATA MOTORS LTD", "SAL982109", "", "82,000.00", "1,12,000.00"),
        ("03-Sep-2024", "03-Sep-2024", "TO TRANSFER-UPI/424691029182/ZEPTO GROCERIES", "UPI4246910", "1,850.00", "", "1,10,150.00"),
        ("05-Sep-2024", "05-Sep-2024", "TO TRANSFER-UPI/424891029381/SWIGGY ONLINE", "UPI4248910", "490.00", "", "1,09,660.00"),
        ("08-Sep-2024", "08-Sep-2024", "BILLPAY AIRTEL POSTPAID MOBILE RECHARGE", "BIL892019", "799.00", "", "1,08,861.00"),
        ("12-Sep-2024", "12-Sep-2024", "TO TRANSFER-UPI/425591029384/UBER INDIA", "UPI4255910", "340.00", "", "1,08,521.00"),
        ("15-Sep-2024", "15-Sep-2024", "ACH DEBIT SBI MUTUAL FUND BLUECHIP EQUITY", "MF901928", "5,000.00", "", "1,03,521.00"),
        ("18-Sep-2024", "18-Sep-2024", "POS 401928 DMART SUPERMARKET SATELLITE", "POS401928", "4,230.00", "", "99,291.00"),
        ("22-Sep-2024", "22-Sep-2024", "ATM CASH WDL-NFS-SBI ATM SATELLITE AHMEDABAD", "ATM391029", "10,000.00", "", "89,291.00"),
        ("25-Sep-2024", "25-Sep-2024", "ACH DEBIT BAJAJ FINANCE CAR LOAN EMI", "EMI482019", "18,400.00", "", "70,891.00"),
        ("28-Sep-2024", "28-Sep-2024", "UPI/427192019283/AMAZON SELLER ECOM/amazon@apl", "UPI4271920", "2,499.00", "", "68,392.00"),
        ("30-Sep-2024", "30-Sep-2024", "ANNUAL MAINTENANCE CHARGES FOR DEBIT CARD", "CHG482019", "236.00", "", "68,156.00"),
        ("30-Sep-2024", "30-Sep-2024", "INTEREST CREDIT FOR Q2 2024 SAVINGS ACCOUNT", "INT892019", "", "294.00", "68,450.00"),
    ]

    for td, vd, desc, ref, dr, cr, bal in sbi_txns:
        rows.append([td, vd, Paragraph(desc, styles['Normal']), ref, dr, cr, bal])

    t_txns = Table(rows, colWidths=[60, 60, 185, 65, 55, 55, 65])
    t_txns.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_txns)
    doc.build(elements)
    return pdf_path


def generate_scanned_image_statement() -> str:
    """
    Renders a statement into images, applies authentic scan degradation
    (grayscale, subtle blur, slight noise), and saves as an image-only PDF.
    """
    # 1. First generate vector PDF to temporary buffer
    temp_pdf = os.path.join(OUT_DIR, "_temp_vector.pdf")
    doc = SimpleDocTemplate(temp_pdf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()

    elements = []
    title_style = ParagraphStyle(
        'BankTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=colors.black,
        spaceAfter=6,
    )
    elements.append(Paragraph("ICICI BANK LIMITED", title_style))
    elements.append(Paragraph("BRANCH: CONNAUGHT PLACE, NEW DELHI - 110001", styles['Normal']))
    elements.append(Spacer(1, 10))

    meta = [
        [Paragraph("<b>Customer:</b> ANANYA SHARMA", styles['Normal']),
         Paragraph("<b>Account No:</b> 001901582910", styles['Normal'])],
        [Paragraph("<b>IFSC:</b> ICIC0000007", styles['Normal']),
         Paragraph("<b>Period:</b> 01/07/2024 to 31/07/2024", styles['Normal'])],
    ]
    elements.append(Table(meta, colWidths=[260, 260]))
    elements.append(Spacer(1, 15))

    txns_data = [
        ["Date", "Description", "Ref No", "Debit", "Credit", "Balance"],
        ["01/07/2024", "SALARY CREDIT - GOOGLE INDIA PAYROLL", "SAL409182", "", "1,20,000.00", "1,55,000.00"],
        ["03/07/2024", "UPI/418491029381/ZOMATO ONLINE FOOD/DR", "UPI4184910", "780.00", "", "1,54,220.00"],
        ["06/07/2024", "UPI/418791029382/BLINKIT QUICK COMMERCE", "UPI4187910", "1,450.00", "", "1,52,770.00"],
        ["10/07/2024", "ELECTRICITY BILL TPDDL DELHI ONLINE", "BIL901928", "3,120.00", "", "1,49,650.00"],
        ["15/07/2024", "POS HPCL AUTO FUEL PETROL CONNAUGHT PL", "POS491029", "4,000.00", "", "1,45,650.00"],
        ["18/07/2024", "ACH DR GROWW INVEST TECH SIP MUTUAL FUND", "MF892019", "10,000.00", "", "1,35,650.00"],
        ["22/07/2024", "ATM CASH WDL ICICI BANK CONNAUGHT PLACE", "ATM901827", "8,000.00", "", "1,27,650.00"],
        ["26/07/2024", "UPI/420791029381/AMAZON SELLER E-COMMERCE", "UPI4207910", "5,290.00", "", "1,22,360.00"],
        ["31/07/2024", "INT.PD:01-07-2024 TO 31-07-2024 SAVINGS", "INT409182", "", "340.00", "1,22,700.00"],
    ]

    elements.append(Table(txns_data, colWidths=[65, 210, 65, 60, 60, 65], style=[
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    doc.build(elements)

    # 2. Render pages to images using pypdfium2
    pdf = pdfium.PdfDocument(temp_pdf)
    scanned_images = []

    for page in pdf:
        img = page.render(scale=2.0).to_pil()
        # Convert to grayscale and apply slight scan contrast
        gray_img = img.convert('L')
        enhancer = ImageEnhance.Contrast(gray_img)
        enhanced = enhancer.enhance(1.1)
        # Convert back to RGB
        scanned_images.append(enhanced.convert('RGB'))

    # 3. Save as pure image-based PDF
    final_scanned_pdf = os.path.join(OUT_DIR, "scanned_sample_statement.pdf")
    if scanned_images:
        scanned_images[0].save(
            final_scanned_pdf,
            save_all=True,
            append_images=scanned_images[1:],
            resolution=150.0,
        )

    # Close pdf document before removing
    pdf.close()
    if os.path.exists(temp_pdf):
        try:
            os.remove(temp_pdf)
        except Exception:
            pass

    return final_scanned_pdf


if __name__ == "__main__":
    h = generate_hdfc_statement()
    print(f"Generated HDFC statement: {h}")
    s = generate_sbi_statement()
    print(f"Generated SBI statement: {s}")
    sc = generate_scanned_image_statement()
    print(f"Generated Scanned statement: {sc}")
