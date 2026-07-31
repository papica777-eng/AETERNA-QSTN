import os
import re
import markdown
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Get custom properties from the canvas or use default
        doc_title = getattr(self, 'doc_title', "AETERNA-SCW Proposal")
        footer_text = getattr(self, 'doc_footer', "CONFIDENTIAL")
        
        # Running header (skip on page 1 for a cleaner cover-like look)
        if self._pageNumber > 1:
            self.drawString(54, 750, f"AETERNA-SCW // {doc_title}")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
        
        # Running footer
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 60, 558, 60)
        self.drawString(54, 45, footer_text)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 45, page_str)
        self.restoreState()

def make_canvas_with_metadata(doc_title, doc_footer):
    class CustomNumberedCanvas(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.doc_title = doc_title
            self.doc_footer = doc_footer
    return CustomNumberedCanvas

def clean_html_text(text):
    # Convert tags to ReportLab supported XML
    text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
    text = text.replace('<em>', '<i>').replace('</em>', '</i>')
    text = text.replace('<code>', '<font face="Courier" color="#1A202C"><b>').replace('</code>', '</b></font>')
    # Format links
    text = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r'<font color="#2B6CB0"><a href="\1"><u>\2</u></a></font>', text)
    # Remove any unsupported HTML tags like 🌊, 🌊, 🛡️, etc. or keep them if they are text
    # Convert some specific emoji unicode to something safe or strip them if needed, but let's keep simple text characters
    text = text.replace('🌊', '').replace('🛡️', '').replace('🎯', '').replace('📋', '').replace('🖋️', '')
    return text.strip()

def html_to_flowables(soup, styles):
    flowables = []
    
    # We walk the children of soup
    body = soup.body if soup.body else soup
    
    def process_node(node, list_level=0, list_type=None, item_num=1):
        nonlocal flowables
        if node.name is None:
            return
            
        if node.name in ['h1', 'h2', 'h3', 'h4']:
            text = clean_html_text(str(node.decode_contents()))
            if node.name == 'h1':
                flowables.append(Spacer(1, 15))
                flowables.append(Paragraph(text, styles['CustomH1']))
                flowables.append(Spacer(1, 10))
            elif node.name == 'h2':
                flowables.append(Spacer(1, 12))
                flowables.append(Paragraph(text, styles['CustomH2']))
                flowables.append(Spacer(1, 8))
            else:
                flowables.append(Spacer(1, 10))
                flowables.append(Paragraph(text, styles['CustomH3']))
                flowables.append(Spacer(1, 6))
                
        elif node.name == 'p':
            text = clean_html_text(str(node.decode_contents()))
            
            # Check if this paragraph contains the signature or keys to embed signature image
            if "[AETERNA_SEC_SOVEREIGN_AUTH_KEY" in text:
                flowables.append(Spacer(1, 15))
                sig_path = "z:\\soul\\docs\\assets\\dimitar_p_signature.png"
                if os.path.exists(sig_path):
                    flowables.append(Image(sig_path, width=120, height=45))
                    flowables.append(Spacer(1, 5))
            
            # Check if it has a partner signature block
            if "[Name of Authorized Representative]" in text:
                flowables.append(Spacer(1, 20))
                # Insert a blank placeholder box for partner signature
                flowables.append(Paragraph("<b>[AUTHORIZED STAMP / SIGNATURE PLACEHOLDER]</b>", styles['CustomH3']))
                flowables.append(Spacer(1, 10))
                
            flowables.append(Paragraph(text, styles['CustomBody']))
            flowables.append(Spacer(1, 6))
            
        elif node.name in ['ul', 'ol']:
            li_nodes = node.find_all('li', recursive=False)
            num = 1
            for li in li_nodes:
                # Find nested lists
                nested_lists = li.find_all(['ul', 'ol'], recursive=False)
                
                # Get text excluding nested lists
                li_text_only = ""
                for child in li.children:
                    if child.name not in ['ul', 'ol']:
                        li_text_only += str(child)
                
                cleaned_text = clean_html_text(li_text_only)
                indent = 15 * (list_level + 1)
                bullet = "&bull;" if node.name == 'ul' else f"{num}."
                
                li_style = ParagraphStyle(
                    f'LiStyle_{list_level}_{node.name}_{num}',
                    parent=styles['CustomBody'],
                    leftIndent=indent,
                    firstLineIndent=-10,
                    spaceAfter=4
                )
                
                flowables.append(Paragraph(f"{bullet} {cleaned_text}", li_style))
                
                for nested in nested_lists:
                    process_node(nested, list_level + 1, nested.name)
                
                num += 1
                
        elif node.name == 'table':
            rows = node.find_all('tr')
            table_data = []
            
            for row in rows:
                row_data = []
                cols = row.find_all(['th', 'td'])
                for col in cols:
                    col_text = clean_html_text(str(col.decode_contents()))
                    is_header = col.name == 'th'
                    cell_style = styles['TableHeader'] if is_header else styles['TableCell']
                    row_data.append(Paragraph(col_text, cell_style))
                table_data.append(row_data)
                
            if table_data:
                col_count = len(table_data[0])
                col_widths = None
                if col_count == 4:
                    col_widths = [140, 75, 189, 100]
                if not col_widths:
                    col_widths = [504 / col_count] * col_count
                    
                t = Table(table_data, colWidths=col_widths)
                t_style = TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),
                    ('TOPPADDING', (0,0), (-1,0), 6),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                    ('TOPPADDING', (0,1), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ])
                for r in range(1, len(table_data)):
                    if r % 2 == 1:
                        t_style.add('BACKGROUND', (0, r), (-1, r), colors.HexColor("#F7FAFC"))
                t.setStyle(t_style)
                flowables.append(Spacer(1, 8))
                flowables.append(t)
                flowables.append(Spacer(1, 10))
                
        elif node.name == 'hr':
            flowables.append(Spacer(1, 5))
            flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=10))
            
        elif node.name == 'pre' or node.name == 'code':
            code_text = node.get_text()
            if "graph TD" in code_text or "mermaid" in code_text:
                flowables.append(Spacer(1, 10))
                flowables.append(Paragraph("<b>AIGIS Subsea Shield - Cyber-Physical Flowchart:</b>", styles['CustomH3']))
                flowables.append(Spacer(1, 6))
                img_path = "z:\\soul\\docs\\assets\\aigis_subsea_shield_flowchart.png"
                if os.path.exists(img_path):
                    flowables.append(Image(img_path, width=480, height=270))
                else:
                    flowables.append(Paragraph("[Flowchart Visualizing AIGIS Subsea Shield Integration]", styles['CustomBody']))
                flowables.append(Spacer(1, 12))
            else:
                clean_code = clean_html_text(node.decode_contents())
                code_style = ParagraphStyle(
                    'CodeBlock',
                    parent=styles['CustomBody'],
                    fontName='Courier',
                    fontSize=8.5,
                    leading=11,
                    textColor=colors.HexColor("#1A202C"),
                    backColor=colors.HexColor("#F7FAFC"),
                    borderColor=colors.HexColor("#E2E8F0"),
                    borderWidth=0.5,
                    borderPadding=8,
                    spaceAfter=8
                )
                flowables.append(Paragraph(clean_code.replace('\n', '<br/>'), code_style))
                
        else:
            for child in node.children:
                process_node(child, list_level, list_type)

    for child in body.children:
        process_node(child)
        
    return flowables

def compile_md_to_pdf(md_file_path, pdf_file_path, doc_title, doc_footer):
    print(f"Compiling: {md_file_path} -> {pdf_file_path}")
    
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
        
    # Convert MD to HTML with tables extension
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Setup document
    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=70,
        bottomMargin=70
    )
    
    # Define custom stylesheet
    styles = getSampleStyleSheet()
    
    custom_styles = {
        'CustomH1': ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1A365D"),
            spaceBefore=18,
            spaceAfter=10,
            keepWithNext=True
        ),
        'CustomH2': ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        ),
        'CustomH3': ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#2D3748"),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True
        ),
        'CustomBody': ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#2D3748"),
            spaceAfter=6
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.white
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#2D3748")
        )
    }
    
    flowables = html_to_flowables(soup, custom_styles)
    
    # Build PDF using NumberedCanvas
    canvas_class = make_canvas_with_metadata(doc_title, doc_footer)
    doc.build(flowables, canvasmaker=canvas_class)
    print(f"Success! Saved PDF at: {pdf_file_path}")

def main():
    pdf_dir = "z:\\soul\\docs\\pdf"
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
        print(f"Created directory: {pdf_dir}")
        
    tasks = [
        {
            "md": "z:\\soul\\docs\\CEF_SMART_CABLES_PROPOSAL.md",
            "pdf": "z:\\soul\\docs\\pdf\\CEF_Part_B_Technical_Description.pdf",
            "title": "Part B Technical Description (WORKS)",
            "footer": "CONFIDENTIAL // CEF DIGITAL 2026 // AETERNA-SCW SMART CABLES WORKS"
        },
        {
            "md": "z:\\soul\\docs\\CEF_SECURITY_COMPLIANCE_DECLARATION.md",
            "pdf": "z:\\soul\\docs\\pdf\\CEF_Security_Compliance_Declaration.pdf",
            "title": "Security Compliance Declaration & Sovereignty Attestation",
            "footer": "EU SOVEREIGN SECURITY ATTESTATION // NIS2 COMPLIANT // PIC 865986222"
        },
        {
            "md": "z:\\soul\\docs\\CEF_LETTER_OF_SUPPORT_TEMPLATE.md",
            "pdf": "z:\\soul\\docs\\pdf\\CEF_Letter_of_Support_Template.pdf",
            "title": "Consortium Letter of Support Template",
            "footer": "CEF DIGITAL 2026 // AETERNA-SCW // CONSORTIUM PARTICIPATION LETTER"
        }
    ]
    
    for t in tasks:
        compile_md_to_pdf(t["md"], t["pdf"], t["title"], t["footer"])

if __name__ == "__main__":
    main()
