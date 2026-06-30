from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer
from transactions.models import Transaction, Currency
from decimal import Decimal
import io
import csv
import datetime
import pandas as pd

# ReportLab imports for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ----------------- PDF GENERATOR HELPER -----------------

def generate_pdf_report(user, title, start_date, end_date, txs):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles matching Glassmorphic Dark/Light Harmonies
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=15
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#6c757d'),
        spaceAfter=25
    )

    h2_style = ParagraphStyle(
        'Heading2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#1e293b')
    )

    # Document Header
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Generated on {datetime.date.today().strftime('%B %d, %Y')} | Period: {start_date} to {end_date} | User: {user.username}", meta_style))
    
    # Financial Calculations
    total_income = Decimal('0.00')
    total_expense = Decimal('0.00')
    
    for t in txs:
        rate = t.currency.exchange_rate_to_usd if t.currency else Decimal('1.0')
        usd_amt = t.amount / rate
        if t.transaction_type == 'Income':
            total_income += usd_amt
        elif t.transaction_type == 'Expense':
            total_expense += usd_amt

    savings = total_income - total_expense
    savings_ratio = (savings / total_income * 100) if total_income > 0 else Decimal('0.0')

    # Summary KPI Grid
    summary_data = [
        [
            Paragraph("<b>Total Income (USD)</b>", body_style),
            Paragraph("<b>Total Expenses (USD)</b>", body_style),
            Paragraph("<b>Net Savings (USD)</b>", body_style),
            Paragraph("<b>Savings Ratio</b>", body_style)
        ],
        [
            f"${total_income:,.2f}",
            f"${total_expense:,.2f}",
            f"${savings:,.2f}",
            f"{savings_ratio:.1f}%"
        ]
    ]
    summary_table = Table(summary_data, colWidths=[130, 130, 130, 130])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#0f172a')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
    ]))
    
    story.append(Paragraph("Financial Summary", h2_style))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Transaction Details Table
    story.append(Paragraph("Detailed Transactions", h2_style))
    
    tx_data = [
        [
            Paragraph("<b>Date</b>", body_style),
            Paragraph("<b>Title</b>", body_style),
            Paragraph("<b>Type</b>", body_style),
            Paragraph("<b>Category</b>", body_style),
            Paragraph("<b>Amount</b>", body_style)
        ]
    ]
    
    for t in txs[:50]: # limit to first 50 transactions to prevent large document blow-up
        symbol = t.currency.symbol if t.currency else '$'
        amt_str = f"{symbol}{t.amount:,.2f}"
        tx_data.append([
            t.date.strftime('%Y-%m-%d'),
            t.title,
            t.transaction_type,
            t.category.name,
            amt_str
        ])
        
    tx_table = Table(tx_data, colWidths=[80, 180, 70, 90, 100])
    tx_table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]
    
    # Alternating row colors
    for i in range(1, len(tx_data)):
        if i % 2 == 0:
            tx_table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
            
    tx_table.setStyle(TableStyle(tx_table_style))
    story.append(tx_table)
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ----------------- HTML VIEWS -----------------

@login_required
def reports_list_view(request):
    user = request.user
    reports = Report.objects.filter(user=user).order_by('-generated_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'generate_report':
            r_type = request.POST.get('report_type')
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            title = f"{r_type} Financial Report ({start_date} - {end_date})"
            
            txs = Transaction.objects.filter(
                user=user, date__range=[start_date, end_date]
            ).select_related('category', 'currency')
            
            pdf_data = generate_pdf_report(user, title, start_date, end_date, txs)
            
            # Save Report record
            rep = Report(
                user=user, title=title, report_type=r_type,
                start_date=start_date, end_date=end_date
            )
            # Save PDF file content
            filename = f"report_{r_type.lower()}_{timezone.now().strftime('%Y%m%d%H%M%S')}.pdf"
            rep.file.save(filename, ContentFile(pdf_data))
            rep.save()
            
            messages.success(request, f"Report '{title}' generated successfully.")
            return redirect('reports_list')

        elif action == 'delete_report':
            r_id = request.POST.get('report_id')
            rep = get_object_or_404(Report, id=r_id, user=user)
            if rep.file:
                rep.file.delete()
            rep.delete()
            messages.success(request, "Report deleted successfully.")
            return redirect('reports_list')

    return render(request, 'reports/reports.html', {
        'reports': reports
    })

# ----------------- REST API VIEWS -----------------

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).order_by('-generated_at')

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_api_report(self, request):
        r_type = request.data.get('report_type', 'Custom')
        start_str = request.data.get('start_date')
        end_str = request.data.get('end_date')
        
        if not start_str or not end_str:
            return Response({'error': 'start_date and end_date required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        start_date = datetime.datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_str, '%Y-%m-%d').date()
        
        title = f"{r_type} Financial Report"
        txs = Transaction.objects.filter(
            user=request.user, date__range=[start_date, end_date]
        ).select_related('category', 'currency')
        
        pdf_data = generate_pdf_report(request.user, title, start_date, end_date, txs)
        
        rep = Report(
            user=request.user, title=title, report_type=r_type,
            start_date=start_date, end_date=end_date
        )
        filename = f"report_api_{timezone.now().strftime('%Y%m%d%H%M%S')}.pdf"
        rep.file.save(filename, ContentFile(pdf_data))
        rep.save()
        
        return Response(ReportSerializer(rep).data, status=status.HTTP_201_CREATED)
