from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
import os
import platform
import re
from datetime import datetime

def get_chinese_font():
    system = platform.system()
    
    if system == 'Windows':
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/simsun.ttc',
        ]
    elif system == 'Darwin':
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
        ]
    else:
        font_paths = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                if font_path.endswith('.ttc'):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
            except Exception as e:
                continue
    
    return 'Helvetica'

_font_name = None

def get_font():
    global _font_name
    if _font_name is None:
        _font_name = get_chinese_font()
    return _font_name

def escape_html(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def parse_markdown_to_elements(text, styles, font_name):
    elements = []
    
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if re.match(r'^#{1,6}\s+', line):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                content = match.group(2)
                content = process_inline_formatting(content)
                
                if level == 1:
                    style = ParagraphStyle('H1', fontName=font_name, fontSize=18, 
                                          textColor=colors.HexColor('#1a1a1a'),
                                          spaceBefore=15, spaceAfter=10, leading=24)
                elif level == 2:
                    style = ParagraphStyle('H2', fontName=font_name, fontSize=16,
                                          textColor=colors.HexColor('#333333'),
                                          spaceBefore=12, spaceAfter=8, leading=22)
                elif level == 3:
                    style = ParagraphStyle('H3', fontName=font_name, fontSize=14,
                                          textColor=colors.HexColor('#444444'),
                                          spaceBefore=10, spaceAfter=6, leading=20)
                else:
                    style = ParagraphStyle('H4', fontName=font_name, fontSize=12,
                                          textColor=colors.HexColor('#555555'),
                                          spaceBefore=8, spaceAfter=4, leading=18)
                
                elements.append(Paragraph(content, style))
            i += 1
        
        elif re.match(r'^[\*\-]\s+', line):
            list_items = []
            while i < len(lines) and re.match(r'^[\*\-]\s+', lines[i]):
                item_text = re.sub(r'^[\*\-]\s+', '', lines[i])
                item_text = process_inline_formatting(item_text)
                list_items.append(item_text)
                i += 1
            
            for item in list_items:
                bullet_style = ParagraphStyle('Bullet', fontName=font_name, fontSize=11,
                                             textColor=colors.HexColor('#333333'),
                                             leftIndent=20, spaceBefore=3, spaceAfter=3, leading=16)
                elements.append(Paragraph(f"• {item}", bullet_style))
        
        elif re.match(r'^\d+\.\s+', line):
            list_items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                item_text = re.sub(r'^\d+\.\s+', '', lines[i])
                item_text = process_inline_formatting(item_text)
                list_items.append(item_text)
                i += 1
            
            for idx, item in enumerate(list_items, 1):
                num_style = ParagraphStyle('Numbered', fontName=font_name, fontSize=11,
                                          textColor=colors.HexColor('#333333'),
                                          leftIndent=20, spaceBefore=3, spaceAfter=3, leading=16)
                elements.append(Paragraph(f"{idx}. {item}", num_style))
        
        elif line.strip() == '':
            i += 1
        
        else:
            paragraph_lines = []
            while i < len(lines) and lines[i].strip() != '' and not re.match(r'^#{1,6}\s+|^[\*\-]\s+|^\d+\.\s+', lines[i]):
                paragraph_lines.append(lines[i])
                i += 1
            
            if paragraph_lines:
                para_text = ' '.join(paragraph_lines)
                para_text = process_inline_formatting(para_text)
                
                body_style = ParagraphStyle('Body', fontName=font_name, fontSize=11,
                                           textColor=colors.HexColor('#333333'),
                                           spaceBefore=6, spaceAfter=6, leading=18)
                elements.append(Paragraph(para_text, body_style))
    
    return elements

def process_inline_formatting(text):
    text = escape_html(text)
    
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    
    text = re.sub(r'`(.+?)`', r'<font face="Courier" color="#666666">\1</font>', text)
    
    return text

def create_pdf_export(
    title: str,
    content: str,
    sources: list = None,
    metadata: dict = None
) -> bytes:
    buffer = io.BytesIO()
    
    font_name = get_font()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceBefore=3,
        spaceAfter=3
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    source_style = ParagraphStyle(
        'SourceStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        leftIndent=10,
        spaceBefore=4,
        spaceAfter=4
    )
    
    story = []
    
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5*cm))
    
    if metadata:
        if metadata.get('session_name'):
            story.append(Paragraph(f"会话: {metadata['session_name']}", meta_style))
        if metadata.get('timestamp'):
            story.append(Paragraph(f"时间: {metadata['timestamp']}", meta_style))
        story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("回答内容", heading_style))
    
    content_elements = parse_markdown_to_elements(content, styles, font_name)
    story.extend(content_elements)
    
    if sources and len(sources) > 0:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("参考来源", heading_style))
        
        for i, source in enumerate(sources, 1):
            filename = source.get('filename', 'Unknown')
            source_content = source.get('content', '')
            
            story.append(Paragraph(f"[{i}] {filename}", source_style))
            if source_content:
                content_preview = source_content[:200] + "..." if len(source_content) > 200 else source_content
                content_preview = escape_html(content_preview)
                story.append(Paragraph(content_preview, source_style))
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
    
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()
