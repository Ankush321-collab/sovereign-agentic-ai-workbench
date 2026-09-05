import os
import datetime
from pathlib import Path
from typing import Dict, Any
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from backend.config import OUTPUTS_DIR

def _set_cell_background(cell, hex_color: str):
    """Sets background color of a table cell."""
    tc_pr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)

def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal cell margins."""
    tc_pr = cell._element.get_or_add_tcPr()
    tc_mar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tc_pr.append(tc_mar)

def generate_psu_approval_note(data: Dict[str, Any], output_filename: str = "PSU_Approval_Note.docx") -> Dict[str, Any]:
    """
    Generates an official Secretariat Green-Sheet Note for Approval in .docx format,
    strictly adhering to Indian Public Sector Undertakings (IOCL/ONGC/GAIL) standards.
    """
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    file_path = OUTPUTS_DIR / output_filename

    doc = docx.Document()

    # Configure Margins (0.75 in)
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.75)
        s.bottom_margin = Inches(0.75)
        s.left_margin = Inches(0.85)
        s.right_margin = Inches(0.85)

    # --- Top PSU Header Banner ---
    p_hdr = doc.add_paragraph()
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_hdr_run = p_hdr.add_run("INDIAN OIL CORPORATION LIMITED\n")
    p_hdr_run.font.name = "Arial"
    p_hdr_run.font.size = Pt(13)
    p_hdr_run.font.bold = True
    p_hdr_run.font.color.rgb = RGBColor(16, 76, 140)

    p_sub = p_hdr.add_run("PIPELINES & REFINERIES DIVISION // HEADQUARTERS\n")
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(9.5)
    p_sub.font.bold = True
    p_sub.font.color.rgb = RGBColor(80, 80, 80)

    p_tag = p_hdr.add_run("SOVEREIGN AIR-GAPPED INTELLIGENCE WORKBENCH // CONFIDENTIAL NOTE SHEET")
    p_tag.font.name = "Arial"
    p_tag.font.size = Pt(8.5)
    p_tag.font.color.rgb = RGBColor(180, 40, 40)

    # Green Secretariat Line
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_after = Pt(12)
    p_line_run = p_line.add_run("―" * 58)
    p_line_run.font.color.rgb = RGBColor(34, 139, 34)
    p_line_run.font.bold = True

    # --- Metadata Table (File No, Date, Department) ---
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    meta_table.cell(0, 0).paragraphs[0].add_run(f"FILE REF NO: {data.get('file_reference_no', 'IOCL/RHQ/PL-MAINT/2026/FL-402')}").bold = True
    meta_table.cell(0, 1).paragraphs[0].add_run(f"DATE: {datetime.datetime.now().strftime('%d-%b-%Y')}").bold = True
    meta_table.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    meta_table.cell(1, 0).paragraphs[0].add_run("ORIGINATING DEPT: Inspection & Integrity Engineering")
    meta_table.cell(1, 1).paragraphs[0].add_run("CLASSIFICATION: RESTRICTED / INTERNAL")
    meta_table.cell(1, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # --- Title / Subject Banner ---
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("NOTE SHEET FOR APPROVAL")
    title_run.font.size = Pt(12.5)
    title_run.font.bold = True
    title_run.font.underline = True

    subj_box = doc.add_table(rows=1, cols=1)
    subj_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    subj_cell = subj_box.cell(0, 0)
    _set_cell_background(subj_cell, "F0F4F8")
    _set_cell_margins(subj_cell, 120, 120, 180, 180)
    sp = subj_cell.paragraphs[0]
    s_label = sp.add_run("SUBJECT: ")
    s_label.bold = True
    s_label.font.color.rgb = RGBColor(16, 76, 140)
    s_text = sp.add_run(data.get("subject", "INTEGRITY ASSESSMENT & REPLACEMENT APPROVAL"))
    s_text.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # --- Helper for numbered sections ---
    def add_section(num: str, title: str, text: str):
        sec_p = doc.add_paragraph()
        sec_p.paragraph_format.space_before = Pt(8)
        sec_p.paragraph_format.space_after = Pt(3)
        r_num = sec_p.add_run(f"{num}. ")
        r_num.bold = True
        r_num.font.color.rgb = RGBColor(16, 76, 140)
        r_title = sec_p.add_run(f"{title}:")
        r_title.bold = True
        r_title.font.color.rgb = RGBColor(16, 76, 140)

        body_p = doc.add_paragraph()
        body_p.paragraph_format.left_indent = Inches(0.3)
        body_p.paragraph_format.space_after = Pt(6)
        body_p.add_run(text)

    # Section 1: Background
    add_section("1", "BACKGROUND & CONTEXT",
                f"During routine ultrasonic thickness gauging and non-destructive testing (NDT) inspection carried out on "
                f"Crude Distillation Unit (CDU-1) high-pressure line, critical thinning was identified on Component {data.get('equipment_tag', 'FL-402')}. "
                f"The component was inspected as part of the annual statutory integrity survey. The observations have been processed "
                f"via on-premises sovereign artificial intelligence workbench without external cloud transmission.")

    # Section 2: Inspection Telemetry Table
    sec2_p = doc.add_paragraph()
    sec2_p.paragraph_format.space_before = Pt(8)
    sec2_p.paragraph_format.space_after = Pt(4)
    r2 = sec2_p.add_run("2. NDT & ULTRASONIC INSPECTION MEASUREMENTS:")
    r2.bold = True
    r2.font.color.rgb = RGBColor(16, 76, 140)

    insp_table = doc.add_table(rows=5, cols=4)
    insp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Component Identifier", "Nominal Thickness", "Measured UT Thickness", "Safety Assessment"]
    for i, h in enumerate(headers):
        c = insp_table.cell(0, i)
        _set_cell_background(c, "104C8C")
        _set_cell_margins(c, 80, 80, 100, 100)
        p = c.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(9)

    tag = data.get("equipment_tag", "FL-402")
    nom = f"{data.get('nominal_thickness_mm', 6.4)} mm"
    act = f"{data.get('measured_thickness_mm', 3.8)} mm"
    ret = f"{data.get('retirement_thickness_mm', 4.2)} mm"
    stat = data.get("compliance_status", "CRITICAL DEFICIT")

    rows_data = [
        [tag, nom, act, stat],
        ["Retirement Threshold (t_min)", ret, f"Margin: {float(data.get('measured_thickness_mm', 3.8)) - float(data.get('retirement_thickness_mm', 4.2)):.2f} mm", "VIOLATION"],
        ["Corrosion Rate", f"{data.get('corrosion_rate_mm_year', 0.45)} mm/year", "Service: 6.2 Years", "ACCELERATED"],
        ["Safe Operating Life Remaining", f"{data.get('remaining_life_years', -0.89)} Years", "Negative Margin", "RETIRE IMMEDIATELY"]
    ]

    for r_idx, r_vals in enumerate(rows_data, 1):
        for c_idx, val in enumerate(r_vals):
            cell = insp_table.cell(r_idx, c_idx)
            _set_cell_margins(cell, 60, 60, 100, 100)
            if r_idx % 2 == 0:
                _set_cell_background(cell, "F9FAFB")
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(8.5)
            if "CRITICAL" in str(val) or "VIOLATION" in str(val) or "RETIRE" in str(val):
                r.bold = True
                r.font.color.rgb = RGBColor(180, 30, 30)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 3: Statutory Standards
    add_section("3", "STATUTORY COMPLIANCE & ENGINEERING STANDARDS",
                f"The measured thickness of {data.get('measured_thickness_mm', 3.8)} mm falls below the minimum allowable retirement thickness "
                f"prescribed under {data.get('statutory_standard', 'ASME B31.3 Section 304.1.2 & OISD-105')}. Barlow's internal design equation "
                f"mandates minimum wall thickness of {data.get('retirement_thickness_mm', 4.2)} mm for 142.5 PSI design envelope. "
                f"Continued operation violates Directorate General of Factory Advice Services and Labour Institutes (DGFASLI) mandates.")

    # Section 4: Operational Risk
    add_section("4", "OPERATIONAL RISK & SAFETY ASSESSMENT",
                data.get("operational_risk", "Severe catastrophic loss-of-containment hazard if line remains under full operating pressure."))

    # Section 5: Financial Implication
    add_section("5", "FINANCIAL ESTIMATE & SANCTION PROPOSAL",
                f"Estimated budget outlay for specialized hot-tapping, spool procurement, replacement flange assembly, and hydrostatic testing is: "
                f"{data.get('financial_estimate_inr', 'INR 14,50,000 (Fourteen Lakhs Fifty Thousand Only)')}. "
                f"The expenditure can be accommodated under Capex Head PL-MAINT-2026/URGENT.")

    # Section 6: Specific Recommendation
    add_section("6", "RECOMMENDATION FOR APPROVAL",
                data.get("recommendation", "Approval is solicited to immediately derate operating pressure and initiate scheduled replacement."))

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # --- Approval Sign-Off Matrix ---
    sign_table = doc.add_table(rows=2, cols=3)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sign_data = [
        ("Initiated by:\n\n__________________\nSr. Inspection Engineer\nDate: " + datetime.datetime.now().strftime("%d-%b-%Y")),
        ("Reviewed & Concurred:\n\n__________________\nChief General Manager (Ops)\nDate: ______________"),
        ("Approved as Proposed:\n\n__________________\nExecutive Director (Refineries)\nDate: ______________")
    ]
    for c_idx, s_text in enumerate(sign_data):
        c = sign_table.cell(0, c_idx)
        _set_cell_background(c, "F5F7FA")
        _set_cell_margins(c, 100, 100, 100, 100)
        p = c.paragraphs[0]
        r = p.add_run(s_text)
        r.font.size = Pt(8.5)

    doc.save(str(file_path))

    return {
        "success": True,
        "filename": output_filename,
        "file_path": str(file_path),
        "file_size": file_path.stat().st_size
    }
