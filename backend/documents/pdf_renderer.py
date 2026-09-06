import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pypdf import PdfReader

from backend.config import OUTPUTS_DIR
from backend.documents.schemas import ArtifactResult

logger = logging.getLogger("pdf_renderer")

def generate_approval_note_pdf(data: Dict[str, Any], output_filename: str = "Approval_Note.pdf") -> Dict[str, Any]:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    file_path = OUTPUTS_DIR / output_filename
    
    warnings_list = []
    
    try:
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        custom_heading = ParagraphStyle(
            'CustomHeading',
            parent=heading_style,
            textColor=colors.HexColor("#104C8C"),
            spaceAfter=10,
            spaceBefore=15
        )
        
        elements = []
        
        # Header
        elements.append(Paragraph("INDIAN OIL CORPORATION LIMITED", title_style))
        elements.append(Paragraph("NOTE SHEET FOR APPROVAL", styles['Heading1']))
        elements.append(Spacer(1, 12))
        
        # Metadata table
        meta_data = [
            [f"FILE REF NO: {data.get('file_reference_no', 'N/A')}", f"DATE: {data.get('date', 'N/A')}"],
            ["ORIGINATING DEPT: Inspection", "CLASSIFICATION: RESTRICTED"]
        ]
        meta_table = Table(meta_data, colWidths=[250, 250])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 12))
        
        # Subject
        elements.append(Paragraph(f"<b>SUBJECT:</b> {data.get('subject', 'N/A')}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Sections
        sections = [
            ("1. BACKGROUND & CONTEXT", data.get('background_summary', '')),
            ("3. STATUTORY COMPLIANCE", data.get('statutory_standard', '')),
            ("4. OPERATIONAL RISK & SAFETY", data.get('operational_risk_assessment', '')),
            ("5. FINANCIAL ESTIMATE", data.get('financial_sanction_inr', '')),
            ("6. RECOMMENDATION", data.get('recommendation_for_approval', ''))
        ]
        
        for title, content in sections:
            if content:
                elements.append(Paragraph(title, custom_heading))
                elements.append(Paragraph(content, normal_style))
                elements.append(Spacer(1, 6))
                
        # Table data (Section 2)
        if "inspection_findings_table" in data and isinstance(data["inspection_findings_table"], list):
            elements.append(Paragraph("2. INSPECTION MEASUREMENTS", custom_heading))
            table_data = [["Component", "Nominal", "Measured", "Status"]]
            for row in data["inspection_findings_table"]:
                if isinstance(row, dict):
                    table_data.append([
                        str(row.get("Component", row.get("component", ""))),
                        str(row.get("Nominal", row.get("nominal", ""))),
                        str(row.get("Measured", row.get("measured", ""))),
                        str(row.get("Status", row.get("status", "")))
                    ])
            if len(table_data) > 1:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#104C8C")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(elements)
        
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return ArtifactResult(
            filename=output_filename,
            file_type="pdf",
            path=str(file_path),
            sha256="",
            validation_status="failed",
            warnings=[f"ReportLab failed: {str(e)}"]
        ).model_dump()
        
    # Validation step
    try:
        if not file_path.exists() or file_path.stat().st_size == 0:
            raise ValueError("File does not exist or is empty")
            
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)
        if num_pages == 0:
            raise ValueError("PDF has 0 pages")
            
        text = reader.pages[0].extract_text()
        if not text.strip():
            warnings_list.append("Text extraction yielded empty string for page 1.")
            
        # Check expected headings
        if "INDIAN OIL" not in text and "NOTE SHEET" not in text:
            warnings_list.append("Missing expected header.")
            
    except Exception as e:
        logger.error(f"Failed to validate generated PDF: {e}")
        return ArtifactResult(
            filename=output_filename,
            file_type="pdf",
            path=str(file_path),
            sha256="",
            validation_status="degraded/failed",
            warnings=[f"Validation failed: {str(e)}"]
        ).model_dump()
        
    # Generate SHA-256
    with open(file_path, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()
        
    return ArtifactResult(
        filename=output_filename,
        file_type="pdf",
        path=str(file_path),
        sha256=sha256_hash,
        validation_status="success" if not warnings_list else "degraded",
        warnings=warnings_list
    ).model_dump()
