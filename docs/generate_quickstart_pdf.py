"""Generate OmniCortex QuickStart PDF with Upgrading section."""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Colors matching existing style
PRIMARY = colors.HexColor('#4A90D9')  # Blue
ACCENT = colors.HexColor('#2ECC71')   # Green
TEXT = colors.HexColor('#333333')
LIGHT_BG = colors.HexColor('#E8F4F8')
CODE_BG = colors.HexColor('#2ECC71')


def header_footer(canvas, doc):
    """Add header and footer to each page."""
    canvas.saveState()
    # Header
    canvas.setFillColor(PRIMARY)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(72, 756, "Quick Start Guide")
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(1)
    canvas.line(72, 750, 540, 750)
    # Footer
    canvas.setFillColor(TEXT)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(306, 30, f"Page {doc.page}")
    canvas.restoreState()


def create_code_block(text):
    """Create a styled code block."""
    data = [[Paragraph(text, ParagraphStyle('Code',
        fontName='Courier', fontSize=10, textColor=colors.white,
        leading=14))]]
    table = Table(data, colWidths=[5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    return table


def create_info_box(title, content):
    """Create an info box with title and content."""
    data = [
        [Paragraph(title, ParagraphStyle('BoxTitle',
            fontName='Helvetica-Bold', fontSize=10, textColor=PRIMARY))],
        [Paragraph(content, ParagraphStyle('BoxContent',
            fontName='Courier', fontSize=9, textColor=TEXT,
            leading=12))]
    ]
    table = Table(data, colWidths=[5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
    ]))
    return table


def build_pdf():
    doc = SimpleDocTemplate(
        "OmniCortex_QuickStart.pdf",
        pagesize=letter,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('Title',
        fontName='Helvetica-Bold', fontSize=28, textColor=PRIMARY,
        spaceAfter=5, alignment=1)
    subtitle_style = ParagraphStyle('Subtitle',
        fontName='Helvetica', fontSize=12, textColor=TEXT,
        spaceAfter=20, alignment=1)
    heading_style = ParagraphStyle('Heading',
        fontName='Helvetica-Bold', fontSize=16, textColor=PRIMARY,
        spaceBefore=20, spaceAfter=10)
    body_style = ParagraphStyle('Body',
        fontName='Helvetica', fontSize=11, textColor=TEXT,
        leading=16, spaceAfter=10)
    bullet_style = ParagraphStyle('Bullet',
        fontName='Helvetica', fontSize=11, textColor=TEXT,
        leading=16, leftIndent=20, bulletIndent=10, spaceAfter=6)

    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Quick Start", title_style))
    elements.append(Paragraph("Get Started in 5 Minutes", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "OmniCortex gives Claude persistent memory across sessions. "
        "This guide will have you up and running in minutes.",
        body_style
    ))
    elements.append(Spacer(1, 15))

    # 1. Installation
    elements.append(Paragraph("1. Installation", heading_style))
    elements.append(create_code_block("pip install omni-cortex"))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Or with optional features:", body_style))
    elements.append(create_code_block(
        "pip install omni-cortex[semantic]  # Semantic search<br/>"
        "pip install omni-cortex[all]       # All features"
    ))
    elements.append(Spacer(1, 15))

    # 2. Upgrading (NEW SECTION)
    elements.append(Paragraph("2. Upgrading", heading_style))
    elements.append(Paragraph(
        "To upgrade to the latest version:",
        body_style
    ))
    elements.append(create_code_block("pip install --upgrade omni-cortex"))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Check your current version:", body_style))
    elements.append(create_code_block("omni-cortex --version"))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "After upgrading, restart your Claude Code session and the dashboard "
        "to use the new features. Your existing memories are preserved.",
        body_style
    ))
    elements.append(Spacer(1, 15))

    # 3. Configure Claude Code (was 2)
    elements.append(Paragraph("3. Configure Claude Code", heading_style))
    elements.append(Paragraph(
        "Add OmniCortex to your Claude Code MCP configuration:",
        body_style
    ))
    elements.append(create_info_box(
        "~/.claude/claude_desktop_config.json:",
        '{\n'
        '  "mcpServers": {\n'
        '    "omni-cortex": {\n'
        '      "command": "omni-cortex",\n'
        '      "args": ["serve"]\n'
        '    }\n'
        '  }\n'
        '}'
    ))
    elements.append(Spacer(1, 15))

    # 4. First Use (was 3)
    elements.append(Paragraph("4. First Use", heading_style))
    elements.append(Paragraph(
        "Start Claude Code in any project directory. OmniCortex will automatically:",
        body_style
    ))
    elements.append(Paragraph("&bull; Create .omni-cortex/ directory in your project", bullet_style))
    elements.append(Paragraph("&bull; Initialize cortex.db SQLite database", bullet_style))
    elements.append(Paragraph("&bull; Make memory tools available to Claude", bullet_style))

    # PAGE BREAK
    elements.append(PageBreak())

    # 5. Core Tools (was 4)
    elements.append(Paragraph("5. Core Tools", heading_style))

    tools_data = [
        ['Tool', 'Purpose', 'Example'],
        ['cortex_remember', 'Store information', 'Store this API pattern'],
        ['cortex_recall', 'Search memories', 'Find auth-related memories'],
        ['cortex_list_memories', 'Browse all', 'Show recent decisions'],
        ['cortex_update_memory', 'Modify memory', 'Add tags to memory'],
        ['cortex_link_memories', 'Create relations', 'Link related solutions'],
    ]

    tools_table = Table(tools_data, colWidths=[1.8*inch, 1.4*inch, 2*inch])
    tools_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tools_table)
    elements.append(Spacer(1, 15))

    # 6. Web Dashboard (was 5)
    elements.append(Paragraph("6. Web Dashboard", heading_style))
    elements.append(create_code_block("omni-cortex-dashboard"))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "Opens a visual interface at http://localhost:8765 for browsing memories, "
        "viewing activity logs, and analyzing your knowledge base.",
        body_style
    ))
    elements.append(Spacer(1, 15))

    # 7. Storage Locations (was 6)
    elements.append(Paragraph("7. Storage Locations", heading_style))

    storage_data = [
        ['Location', 'Path', 'Purpose'],
        ['Project DB', '.omni-cortex/cortex.db', 'Project memories & activities'],
        ['Global DB', '~/.omni-cortex/global.db', 'Cross-project search index'],
        ['Project Config', '~/.omni-cortex/projects.json', 'Dashboard settings & favorites'],
    ]

    storage_table = Table(storage_data, colWidths=[1.3*inch, 2.2*inch, 2*inch])
    storage_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(storage_table)
    elements.append(Spacer(1, 15))

    # 8. Memory Types (was 7)
    elements.append(Paragraph("8. Memory Types", heading_style))

    types_data = [
        ['Type', 'Use For'],
        ['fact', 'Technical facts, API details, configurations'],
        ['decision', 'Architectural choices, design decisions'],
        ['solution', 'Working fixes, implementation patterns'],
        ['error', 'Error resolutions, debugging insights'],
        ['progress', 'Current state, work in progress'],
        ['preference', 'User preferences, coding style choices'],
    ]

    types_table = Table(types_data, colWidths=[1.2*inch, 4*inch])
    types_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(types_table)

    # PAGE BREAK
    elements.append(PageBreak())

    # 9. Pro Tips (was 8)
    elements.append(Paragraph("9. Pro Tips", heading_style))
    elements.append(Paragraph('&bull; Ask Claude to "remember this" when you solve a tricky problem', bullet_style))
    elements.append(Paragraph("&bull; Use tags liberally - they're searchable and filterable", bullet_style))
    elements.append(Paragraph("&bull; Link related memories to build a knowledge graph", bullet_style))
    elements.append(Paragraph("&bull; Review stale memories periodically (use the Review tab)", bullet_style))
    elements.append(Paragraph("&bull; Export memories before major refactoring", bullet_style))
    elements.append(Paragraph("&bull; Use the global index for cross-project patterns", bullet_style))
    elements.append(Spacer(1, 20))

    # Next Steps
    elements.append(Paragraph("Next Steps", heading_style))
    elements.append(Paragraph("Now that you're set up, explore these resources:", body_style))
    elements.append(Paragraph("&bull; <b>Command Reference</b> - Full tool documentation", bullet_style))
    elements.append(Paragraph("&bull; <b>Dashboard Guide</b> - Visual interface walkthrough", bullet_style))
    elements.append(Paragraph("&bull; <b>Storage Architecture</b> - Technical deep dive", bullet_style))
    elements.append(Spacer(1, 30))

    # Footer banner
    footer_data = [[Paragraph(
        '<b>OmniCortex</b> | github.com/AllCytes/Omni-Cortex',
        ParagraphStyle('Footer', fontName='Helvetica', fontSize=10,
                      textColor=colors.white, alignment=1)
    )]]
    footer_table = Table(footer_data, colWidths=[5.5*inch])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(footer_table)

    # Build PDF
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    print("Generated: OmniCortex_QuickStart.pdf")


if __name__ == "__main__":
    build_pdf()
