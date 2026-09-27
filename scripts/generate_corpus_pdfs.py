"""
Robust script to generate PDF versions of selected HR policies in data/policy_corpus/
using fpdf2. Multi-format corpus ingestion (Markdown + PDF).
"""

import os
from pathlib import Path
from fpdf import FPDF

class PolicyPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, 'Quantic Global Enterprises - Official HR Policy Document', new_x="LMARGIN", new_y="NEXT", align='R')
        self.ln(4)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def sanitize_text(text: str) -> str:
    """Sanitize unicode characters into latin-1 equivalents for standard fonts."""
    replacements = {
        '\u2014': ' -- ',
        '\u2013': '-',
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2022': '*',
        '\u2026': '...',
        '**': '',
        '__': ''
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode('latin-1', 'replace').decode('latin-1')

def convert_md_to_pdf(md_path: Path, pdf_path: Path):
    pdf = PolicyPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.add_page()
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for raw_line in lines:
        line = sanitize_text(raw_line.strip())
        if not line:
            pdf.ln(3)
            continue
            
        if line.startswith('---'):
            pdf.ln(2)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(4)
            continue

        if line.startswith('# '):
            pdf.set_font('Helvetica', 'B', 15)
            pdf.set_text_color(24, 43, 73)
            title = line[2:].strip()
            pdf.multi_cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif line.startswith('## '):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(33, 70, 139)
            heading = line[3:].strip()
            pdf.ln(2)
            pdf.multi_cell(0, 6, heading, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif line.startswith('### '):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(60, 60, 60)
            sub = line[4:].strip()
            pdf.multi_cell(0, 5, sub, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif line.startswith('* ') or line.startswith('- '):
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(40, 40, 40)
            bullet_text = line[2:].strip()
            pdf.multi_cell(0, 5, f"- {bullet_text}", new_x="LMARGIN", new_y="NEXT")
        elif len(line) > 3 and line[0].isdigit() and line[1] in ('.', ')'):
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
            
    pdf.output(str(pdf_path))
    print(f"Generated PDF: {pdf_path.name}")

def main():
    corpus_dir = Path(__file__).resolve().parent.parent / "data" / "policy_corpus"
    target_docs = [
        "DOC-002_remote_work_policy.md",
        "DOC-005_employee_benefits_guide.md",
        "DOC-008_parental_and_fmla_leave.md",
        "DOC-012_substance_abuse_drug_free_workplace.md",
        "DOC-016_cybersecurity_incident_response_gdpr.md"
    ]
    
    for doc in target_docs:
        md_file = corpus_dir / doc
        if md_file.exists():
            pdf_file = corpus_dir / (md_file.stem + ".pdf")
            convert_md_to_pdf(md_file, pdf_file)
            os.remove(md_file)
            print(f"Replaced {md_file.name} with {pdf_file.name}")

if __name__ == "__main__":
    main()
