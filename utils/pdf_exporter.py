# utils/pdf_exporter.py

import io
import re
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from state.travel_state import TravelState


class TravelPDFExporter:
    """
    Generates professional travel itinerary PDFs with all planning sections.
    Designed to be extensible for future sections like flights, car rentals, etc.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._setup_custom_styles()
    
    def _register_fonts(self):
        """Register Unicode-compatible fonts for better character support"""
        try:
            # Try to register DejaVu fonts for better Unicode support
            # These are commonly available on most systems
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
            self.unicode_font = 'DejaVuSans'
            self.unicode_font_bold = 'DejaVuSans-Bold'
        except:
            # Fallback to default fonts if DejaVu not available
            self.unicode_font = 'Helvetica'
            self.unicode_font_bold = 'Helvetica-Bold'
    
    def _setup_custom_styles(self):
        """Define custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='TravelTitle',
            parent=self.styles['Title'],
            fontName=self.unicode_font_bold,
            fontSize=24,
            spaceAfter=20,
            textColor=HexColor('#2E86AB'),
            alignment=1  # Center
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontName=self.unicode_font_bold,
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=HexColor('#A23B72'),
            borderWidth=1,
            borderColor=HexColor('#A23B72'),
            borderPadding=8
        ))
        
        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading2'],
            fontName=self.unicode_font_bold,
            fontSize=14,
            spaceBefore=12,
            spaceAfter=8,
            textColor=HexColor('#F18F01')
        ))
        
        # Content style
        self.styles.add(ParagraphStyle(
            name='TravelContent',
            parent=self.styles['Normal'],
            fontName=self.unicode_font,
            fontSize=10,
            spaceBefore=6,
            spaceAfter=6,
            leftIndent=10
        ))
    
    def _clean_markdown_text(self, text: str) -> str:
        """Clean markdown formatting and fix character encoding for PDF display"""
        if not text:
            return ""
        
        # Fix common problematic characters first
        char_replacements = {
            '–': '-',           # En dash
            '—': '--',          # Em dash
            ''': "'",           # Left single quote
            ''': "'",           # Right single quote
            '"': '"',           # Left double quote
            '"': '"',           # Right double quote
            '…': '...',         # Ellipsis
            '•': '• ',          # Bullet point (keep but ensure space)
            '★': '*',           # Star
            '✓': 'v',           # Checkmark
            '✗': 'x',           # X mark
            '€': 'EUR',         # Euro symbol
            '£': 'GBP',         # Pound symbol
            '¥': 'JPY',         # Yen symbol
            '°': ' degrees',    # Degree symbol
        }
        
        for old_char, new_char in char_replacements.items():
            text = text.replace(old_char, new_char)
        
        # Remove any remaining non-ASCII characters that might cause issues
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        # Remove markdown headers and replace with simple formatting
        text = re.sub(r'^#{1,6}\s*(.+?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
        
        # Convert markdown bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        
        # Handle bullet points (ensure consistent formatting)
        text = re.sub(r'^[-•]\s*(.+?)$', r'• \1', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        
        return text.strip()
    
    def _add_section(self, story: list, title: str, content: str, icon: str = ""):
        """Add a formatted section to the PDF story"""
        if not content:
            return
        
        # Section header
        header_text = f"{icon} {title}" if icon else title
        story.append(Paragraph(header_text, self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Clean and format content
        cleaned_content = self._clean_markdown_text(content)
        
        # Split content into paragraphs
        paragraphs = cleaned_content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), self.styles['TravelContent']))
                story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
    
    def generate_pdf(self, state: TravelState, result: Dict[str, Any]) -> bytes:
        """
        Generate a comprehensive travel PDF from state and results.
        
        Args:
            state: Original travel state with user inputs
            result: Generated results from all agents
            
        Returns:
            PDF bytes for download
        """
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        # Build story (content)
        story = []
        
        # Title page
        destination = state.get("destination", "Unknown Destination")
        start_date = state.get("start_date", datetime.now().date())
        end_date = state.get("end_date", datetime.now().date())
        
        story.append(Paragraph(f"Travel Itinerary", self.styles['TravelTitle']))
        story.append(Paragraph(f"{destination}", self.styles['Heading1']))
        story.append(Paragraph(
            f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}", 
            self.styles['Heading2']
        ))
        story.append(Spacer(1, 0.5*inch))
        
        # Trip overview
        trip_nights = (end_date - start_date).days
        overview = f"""
        <b>Trip Overview:</b><br/>
        • Destination: {destination}<br/>
        • Duration: {trip_nights} nights<br/>
        • Travelers: {state.get('num_people', 1)} people<br/>
        • Budget: {state.get('budget_type', 'mid-range').title()}<br/>
        • Trip Style: {state.get('trip_type', 'cultural').title()}<br/>
        • Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        """
        story.append(Paragraph(overview, self.styles['TravelContent']))
        story.append(Spacer(1, 0.5*inch))
        
        # Define sections in order (extensible for future additions)
        sections = [
            (" Visa Information", result.get("visa_info")),
            (" Weather Forecast", result.get("weather_forecast")),
            (" Travel Itinerary", result.get("itinerary")),
            (" Hotel Recommendations", result.get("suggested_hotels")),
            (" Suggested Activities", result.get("suggested_activities")),
            # Future sections can be easily added here:
            # ("✈️ Flight Information", result.get("flight_info")),
            # ("🚗 Transportation", result.get("transportation_info")),
            # ("📋 Packing List", result.get("packing_list")),
        ]
        
        # Add each section
        for title, content in sections:
            if content:
                self._add_section(story, title.split(' ', 1)[1], content, title.split(' ')[0])
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"Generated by AI Travel Planner on {datetime.now().strftime('%B %d, %Y')}"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes


def export_travel_pdf(state: TravelState, result: Dict[str, Any]) -> bytes:
    """
    Convenience function to export travel plan as PDF.
    
    Args:
        state: Travel state with user inputs
        result: Generated results from workflow
        
    Returns:
        PDF bytes ready for download
    """
    exporter = TravelPDFExporter()
    return exporter.generate_pdf(state, result)