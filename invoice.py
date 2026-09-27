from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

def calculate_invoice(items, tax_rate):
    subtotal = 0
    calculated_items = []

    for item in items:
        if not item["found"]:
            continue

        amount = item["quantity"] * item["unit_price"]
        subtotal += amount

        calculated_items.append({**item, "amount": amount})

    tax_amount = subtotal * tax_rate / 100
    total = subtotal + tax_amount

    return {
        "items": calculated_items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total": total,
    }

def generate_invoice_number():
    return "INV-" + datetime.now().strftime("%Y%m%d-%H%M%S")

def generate_pdf(invoice_number, customer_name, customer_email,
                 items, subtotal, tax_rate, tax_amount, total, notes=""):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InvoiceTitle", parent=styles["Title"],
        alignment=TA_CENTER, fontSize=24, spaceAfter=10
    )
    normal_style = ParagraphStyle(
        "NormalCustom", parent=styles["Normal"],
        fontSize=10, leading=14
    )
    right_style = ParagraphStyle(
        "Right", parent=styles["Normal"],
        alignment=TA_RIGHT, fontSize=10
    )

    story = [
        Paragraph("INVOICE", title_style),
        Paragraph(
            "<b>InvoicePilot AI</b><br/>AI-Powered Invoice Automation",
            normal_style,
        ),
        Spacer(1, 15),
    ]

    header_table = Table(
        [[
            Paragraph(
                f"<b>Bill To</b><br/>{customer_name or 'Not provided'}<br/>"
                f"{customer_email or 'Not provided'}",
                normal_style,
            ),
            Paragraph(
                f"<b>Invoice:</b> {invoice_number}<br/>"
                f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}",
                right_style,
            ),
        ]],
        colWidths=[95 * mm, 75 * mm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story += [header_table, Spacer(1, 20)]

    table_data = [["Service", "Description", "Qty", "Unit Price", "Amount"]]
    for item in items:
        table_data.append([
            item["matched_name"],
            item["description"] or "",
            str(item["quantity"]),
            f"₹{item['unit_price']:,.2f}",
            f"₹{item['amount']:,.2f}",
        ])

    service_table = Table(
        table_data,
        colWidths=[38 * mm, 57 * mm, 15 * mm, 30 * mm, 30 * mm],
        repeatRows=1,
    )
    service_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [service_table, Spacer(1, 20)]

    totals_table = Table(
        [
            ["Subtotal", f"₹{subtotal:,.2f}"],
            [f"GST ({tax_rate:.0f}%)", f"₹{tax_amount:,.2f}"],
            ["TOTAL", f"₹{total:,.2f}"],
        ],
        colWidths=[130 * mm, 40 * mm],
    )
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 2), (-1, 2), 12),
        ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)

    if notes:
        story += [
            Spacer(1, 20),
            Paragraph(f"<b>Notes:</b> {notes}", normal_style),
        ]

    story += [
        Spacer(1, 30),
        Paragraph(
            "Generated using InvoicePilot AI",
            ParagraphStyle(
                "Footer", parent=styles["Normal"],
                alignment=TA_CENTER, fontSize=8
            ),
        ),
    ]

    document.build(story)
    buffer.seek(0)
    return buffer
