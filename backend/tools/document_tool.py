from pathlib import Path
import logging
from backend.config import OUTPUTS_DIR
from backend.services.multimodal_service import MultimodalService

logger = logging.getLogger("document_tool")

def generate_docx(title: str, content: str, output_filename: str = "Approval_Note.docx") -> dict:
    """Generates an executive/industrial Word (.docx) document deliverable."""
    output_path = OUTPUTS_DIR / output_filename
    try:
        import docx
        from docx.shared import Inches, Pt, RGBColor
        
        doc = docx.Document()
        
        # Heading
        heading = doc.add_heading(title, level=1)
        
        # Subheading / Metadata
        meta_para = doc.add_paragraph()
        r = meta_para.add_run("Sovereign AI Workbench — Official Confidential Deliverable\n")
        r.font.size = Pt(9)
        r.font.italic = True
        r.font.color.rgb = RGBColor(100, 100, 100)
        
        # Body Content
        for paragraph_text in content.split("\n\n"):
            if paragraph_text.strip():
                doc.add_paragraph(paragraph_text.strip())
                
        doc.save(str(output_path))
        return {
            "success": True,
            "filename": output_path.name,
            "file_path": str(output_path),
            "message": f"Successfully generated DOCX document: {output_path.name}"
        }
    except Exception as e:
        logger.warning(f"python-docx generation failed ({e}), writing text file fallback.")
        txt_path = output_path.with_suffix(".txt")
        txt_path.write_text(f"{title}\n\n{content}", encoding="utf-8")
        return {
            "success": True,
            "filename": txt_path.name,
            "file_path": str(txt_path),
            "message": f"Generated text document fallback: {txt_path.name}"
        }

def generate_pptx(title: str, slide_titles: list[str], slide_contents: list[str], output_filename: str = "Report.pptx") -> dict:
    """Generates a PowerPoint (.pptx) presentation deliverable."""
    output_path = OUTPUTS_DIR / output_filename
    try:
        from pptx import Presentation
        prs = Presentation()
        
        # Title Slide
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        title_box = slide.shapes.title
        subtitle_box = slide.placeholders[1]
        title_box.text = title
        subtitle_box.text = "Confidential Industrial Summary — Sovereign AI Workbench"
        
        # Bullet Slides
        bullet_slide_layout = prs.slide_layouts[1]
        for t, c in zip(slide_titles, slide_contents):
            s = prs.slides.add_slide(bullet_slide_layout)
            s.shapes.title.text = t
            tf = s.placeholders[1].text_frame
            tf.text = c
            
        prs.save(str(output_path))
        return {
            "success": True,
            "filename": output_path.name,
            "file_path": str(output_path),
            "message": f"Successfully generated PPTX document: {output_path.name}"
        }
    except Exception as e:
        logger.warning(f"python-pptx generation failed ({e}), writing fallback markdown.")
        md_path = output_path.with_suffix(".md")
        md_content = f"# {title}\n\n"
        for t, c in zip(slide_titles, slide_contents):
            md_content += f"## {t}\n{c}\n\n"
        md_path.write_text(md_content, encoding="utf-8")
        return {
            "success": True,
            "filename": md_path.name,
            "file_path": str(md_path),
            "message": f"Generated Markdown presentation fallback: {md_path.name}"
        }

def edit_spreadsheet(rows: list[list], output_filename: str = "Calculation.xlsx") -> dict:
    """Generates or updates an Excel (.xlsx) spreadsheet deliverable."""
    output_path = OUTPUTS_DIR / output_filename
    try:
        import pandas as pd
        if rows and len(rows) > 1:
            df = pd.DataFrame(rows[1:], columns=rows[0])
        else:
            df = pd.DataFrame(rows)
        df.to_excel(str(output_path), index=False)
        return {
            "success": True,
            "filename": output_path.name,
            "file_path": str(output_path),
            "message": f"Successfully generated Excel spreadsheet: {output_path.name}"
        }
    except Exception as e:
        logger.warning(f"pandas/openpyxl generation failed ({e}), writing CSV fallback.")
        csv_path = output_path.with_suffix(".csv")
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return {
            "success": True,
            "filename": csv_path.name,
            "file_path": str(csv_path),
            "message": f"Generated CSV spreadsheet fallback: {csv_path.name}"
        }

async def ocr_document(file_path: str) -> dict:
    """Runs OCR and visual layout extraction on a document."""
    return await MultimodalService.process_document(file_path)
