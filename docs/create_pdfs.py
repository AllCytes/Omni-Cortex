#!/usr/bin/env python3
"""Create OmniCortex teaching material PDFs with light theme."""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# === LIGHT THEME COLORS ===
PRIMARY = colors.HexColor('#2563EB')      # Blue
SECONDARY = colors.HexColor('#7C3AED')    # Purple
ACCENT = colors.HexColor('#10B981')       # Green
TEXT_DARK = colors.HexColor('#1F2937')    # Dark gray
TEXT_MUTED = colors.HexColor('#6B7280')   # Medium gray
BG_LIGHT = colors.HexColor('#F3F4F6')     # Light gray
BG_ACCENT = colors.HexColor('#EEF2FF')    # Very light blue
WHITE = colors.white


def create_styles():
    """Create consistent styles for all documents."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'OCDocTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=4,
        leading=34
    ))

    styles.add(ParagraphStyle(
        'OCDocSubtitle',
        fontName='Helvetica',
        fontSize=12,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=30,
        leading=16
    ))

    styles.add(ParagraphStyle(
        'OCSectionTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=PRIMARY,
        spaceBefore=20,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        'OCSubSection',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=SECONDARY,
        spaceBefore=15,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        'OCBody',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_DARK,
        leading=14,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        'OCBulletItem',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_DARK,
        leading=14,
        leftIndent=20,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'OCCode',
        fontName='Courier',
        fontSize=9,
        textColor=TEXT_DARK,
        backColor=BG_LIGHT,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        'OCCallout',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=WHITE,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'OCFooter',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER
    ))

    return styles


def header_footer(canvas, doc, title="OmniCortex Memory MCP"):
    """Draw consistent header and footer."""
    canvas.saveState()
    width, height = letter

    # Header line
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(50, height - 40, width - 50, height - 40)

    # Header text
    canvas.setFillColor(PRIMARY)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(50, height - 32, title)

    # Footer line
    canvas.setStrokeColor(BG_LIGHT)
    canvas.setLineWidth(1)
    canvas.line(50, 35, width - 50, 35)

    # Page number
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(width / 2, 20, f"Page {doc.page}")

    canvas.restoreState()


def create_callout_box(text, color=PRIMARY):
    """Create a colored callout box."""
    data = [[Paragraph(text, ParagraphStyle('CalloutText',
        fontName='Helvetica-Bold', fontSize=10, textColor=WHITE, alignment=TA_CENTER))]]
    table = Table(data, colWidths=[5.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return table


def create_feature_box(title, items, color=PRIMARY):
    """Create a feature box with title and bullet items."""
    content = []
    content.append(Paragraph(f"<b>{title}</b>", ParagraphStyle('BoxTitle',
        fontName='Helvetica-Bold', fontSize=11, textColor=color)))
    for item in items:
        content.append(Paragraph(f"• {item}", ParagraphStyle('BoxItem',
            fontName='Helvetica', fontSize=9, textColor=TEXT_DARK, leftIndent=10, leading=12)))

    data = [[content]]
    table = Table(data, colWidths=[2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_ACCENT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBEFORE', (0, 0), (0, -1), 3, color),
    ]))
    return table


# === DOCUMENT 1: QUICK START GUIDE ===
def create_quickstart_pdf():
    """Create the Quick Start Guide PDF."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_QuickStart.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=60, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    # === PAGE 1: What is OmniCortex? ===
    elements.append(Paragraph("OmniCortex Memory MCP", styles['OCDocTitle']))
    elements.append(Paragraph("Quick Start Guide", styles['OCDocSubtitle']))

    elements.append(Paragraph("What is OmniCortex?", styles['OCSectionTitle']))
    elements.append(Paragraph(
        "OmniCortex is a <b>universal memory system</b> for Claude Code that stores what you learn, "
        "tracks what you do, and helps you never repeat the same mistakes twice.",
        styles['OCBody']
    ))

    elements.append(Spacer(1, 10))
    elements.append(create_callout_box(
        '"Store everything important so you never repeat mistakes"',
        SECONDARY
    ))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Unlike Basic Memory MCPs", styles['OCSubSection']))
    elements.append(Paragraph("• <b>Activity Logging</b> - Full audit trail of every tool call", styles['OCBulletItem']))
    elements.append(Paragraph("• <b>Session Continuity</b> - \"Last time you were working on...\" context", styles['OCBulletItem']))
    elements.append(Paragraph("• <b>Cross-Project Search</b> - Find knowledge from any project", styles['OCBulletItem']))
    elements.append(Paragraph("• <b>Auto-Categorization</b> - Intelligent memory type detection", styles['OCBulletItem']))
    elements.append(Paragraph("• <b>Importance Decay</b> - Frequently accessed memories surface first", styles['OCBulletItem']))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Installation (2 Commands)", styles['OCSubSection']))

    install_data = [
        [Paragraph("<b>Step 1:</b> Install the package", styles['OCBody'])],
        [Paragraph("pip install omni-cortex", styles['OCCode'])],
        [Paragraph("<b>Step 2:</b> Run automatic setup", styles['OCBody'])],
        [Paragraph("omni-cortex-setup", styles['OCCode'])],
    ]
    install_table = Table(install_data, colWidths=[5.5*inch])
    install_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(install_table)

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        "For AI-powered semantic search: <b>pip install omni-cortex[semantic]</b>",
        styles['OCBody']
    ))

    # === PAGE 2: Core Features ===
    elements.append(PageBreak())
    elements.append(Paragraph("Core Features", styles['OCSectionTitle']))

    # Tool categories table
    tool_data = [
        ['Category', 'Count', 'Purpose'],
        ['Memory Tools', '6', 'Store, search, update, delete memories'],
        ['Activity Tools', '3', 'Log and query tool usage'],
        ['Session Tools', '3', 'Manage work sessions with context'],
        ['Utility Tools', '3', 'Tags, reviews, exports'],
        ['Global Tools', '3', 'Cross-project search and sync'],
    ]
    tool_table = Table(tool_data, colWidths=[1.8*inch, 0.8*inch, 3*inch])
    tool_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(tool_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Dual-Layer Storage", styles['OCSubSection']))

    # Two column layout for dual storage
    storage_left = create_feature_box("Activity Log", [
        "What tools were used",
        "Success/failure status",
        "Duration and timing",
        "Automatic via hooks"
    ], PRIMARY)

    storage_right = create_feature_box("Knowledge Store", [
        "Solutions found",
        "Decisions made",
        "Warnings learned",
        "Searchable insights"
    ], SECONDARY)

    storage_table = Table([[storage_left, Spacer(1, 10), storage_right]],
                          colWidths=[2.6*inch, 0.3*inch, 2.6*inch])
    storage_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(storage_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Smart Features", styles['OCSubSection']))
    elements.append(Paragraph(
        "<b>Session Continuity:</b> When you start a new session, OmniCortex provides context from your "
        "previous sessions - what you were working on, key decisions made, and where you left off.",
        styles['OCBody']
    ))
    elements.append(Paragraph(
        "<b>Auto-Categorization:</b> Memories are automatically tagged with types like 'solution', "
        "'warning', 'config', 'troubleshooting' based on their content.",
        styles['OCBody']
    ))
    elements.append(Paragraph(
        "<b>Hybrid Search:</b> Combines keyword matching (FTS5) with optional AI-powered semantic search "
        "for finding memories by meaning, not just exact words.",
        styles['OCBody']
    ))

    # === PAGE 3: Getting Started ===
    elements.append(PageBreak())
    elements.append(Paragraph("Getting Started", styles['OCSectionTitle']))

    elements.append(Paragraph("Essential Commands", styles['OCSubSection']))

    cmd_data = [
        ['Command', 'What It Does'],
        ['cortex_remember', 'Store important information with auto-categorization'],
        ['cortex_recall', 'Search your memories by keyword or meaning'],
        ['cortex_start_session', 'Begin a work session and get previous context'],
        ['cortex_global_search', 'Search memories across ALL your projects'],
        ['cortex_list_memories', 'Browse memories with filters and sorting'],
        ['cortex_get_timeline', 'See chronological history of activities'],
    ]
    cmd_table = Table(cmd_data, colWidths=[2*inch, 3.5*inch])
    cmd_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(cmd_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Token/Context Usage", styles['OCSubSection']))
    elements.append(Paragraph(
        "• <b>Initial Load:</b> ~2KB for tool schemas (18 tools registered)",
        styles['OCBulletItem']
    ))
    elements.append(Paragraph(
        "• <b>Per Tool Call:</b> Minimal overhead, results returned as formatted markdown",
        styles['OCBulletItem']
    ))
    elements.append(Paragraph(
        "• <b>Memory Storage:</b> SQLite database, no token cost for stored memories",
        styles['OCBulletItem']
    ))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Storage Locations", styles['OCSubSection']))
    storage_loc_data = [
        ['Location', 'Path', 'Purpose'],
        ['Per-Project', '.omni-cortex/cortex.db', 'Project-specific memories'],
        ['Global Index', '~/.omni-cortex/global.db', 'Cross-project search'],
        ['Config', '.omni-cortex/config.yaml', 'Project settings'],
    ]
    storage_loc_table = Table(storage_loc_data, colWidths=[1.3*inch, 2.2*inch, 2*inch])
    storage_loc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(storage_loc_table)
    elements.append(Spacer(1, 20))

    elements.append(create_callout_box(
        "Restart Claude Code after installation to activate OmniCortex",
        ACCENT
    ))

    # Build PDF
    doc.build(elements, onFirstPage=lambda c, d: header_footer(c, d, "Quick Start Guide"),
              onLaterPages=lambda c, d: header_footer(c, d, "Quick Start Guide"))
    print("Created: OmniCortex_QuickStart.pdf")


# === DOCUMENT 2: FEATURE COMPARISON ===
def create_comparison_pdf():
    """Create the Feature Comparison PDF."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_FeatureComparison.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=60, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    elements.append(Paragraph("OmniCortex vs Basic Memory MCPs", styles['OCDocTitle']))
    elements.append(Paragraph("Feature Comparison Guide", styles['OCDocSubtitle']))

    elements.append(Paragraph("The Evolution of Memory Systems", styles['OCSectionTitle']))
    elements.append(Paragraph(
        "Basic memory MCPs provide simple remember/recall functionality. OmniCortex builds on this "
        "foundation with enterprise-grade features for serious development workflows.",
        styles['OCBody']
    ))

    elements.append(Spacer(1, 15))

    # Comparison table
    compare_data = [
        ['Feature', 'Basic Memory MCP', 'OmniCortex'],
        ['Store memories', '✓', '✓'],
        ['Search memories', 'Simple keyword', 'FTS5 + Semantic + Hybrid'],
        ['Activity logging', '—', '✓ Automatic via hooks'],
        ['Session continuity', '—', '✓ "Last time you were..."'],
        ['Cross-project search', '—', '✓ Global index'],
        ['Auto-categorization', '—', '✓ 11 memory types'],
        ['Memory relationships', '—', '✓ Link related memories'],
        ['Importance decay', '—', '✓ Smart ranking'],
        ['Export formats', 'JSON only', 'Markdown, JSON, SQLite'],
        ['Memory freshness', '—', '✓ Review & archive'],
        ['Tool count', '2-4', '18 tools'],
    ]

    compare_table = Table(compare_data, colWidths=[2.2*inch, 1.6*inch, 1.8*inch])
    compare_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (2, 1), (2, -1), ACCENT),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
    ]))
    elements.append(compare_table)
    elements.append(Spacer(1, 25))

    elements.append(Paragraph("Key Differentiators", styles['OCSectionTitle']))

    diff_items = [
        ("Activity Logging", "Every tool call is automatically logged with timestamps, duration, "
         "success/failure status, and context. This creates a complete audit trail of your development sessions."),
        ("Session Management", "Start sessions to get context from previous work. End sessions with summaries "
         "and key learnings that persist across restarts."),
        ("Multi-Factor Ranking", "Memories are ranked by relevance, importance score, access frequency, "
         "and recency - not just keyword matching."),
        ("Memory Types", "11 auto-detected types: solution, warning, config, troubleshooting, code, "
         "error, command, concept, decision, tip, general."),
        ("Relationship Links", "Connect related memories with supersedes, derived_from, related_to, "
         "or contradicts relationships."),
    ]

    for title, desc in diff_items:
        elements.append(Paragraph(f"<b>{title}</b>", styles['OCSubSection']))
        elements.append(Paragraph(desc, styles['OCBody']))

    # Build PDF
    doc.build(elements, onFirstPage=lambda c, d: header_footer(c, d, "Feature Comparison"),
              onLaterPages=lambda c, d: header_footer(c, d, "Feature Comparison"))
    print("Created: OmniCortex_FeatureComparison.pdf")


# === DOCUMENT 3: PHILOSOPHY & INSPIRATION ===
def create_philosophy_pdf():
    """Create the Philosophy & Inspiration PDF."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_Philosophy.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=60, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    elements.append(Paragraph("The Philosophy Behind OmniCortex", styles['OCDocTitle']))
    elements.append(Paragraph("Design Principles & Inspiration", styles['OCDocSubtitle']))

    elements.append(Paragraph("Two Key Inspirations", styles['OCSectionTitle']))
    elements.append(Paragraph(
        "OmniCortex was built by combining insights from two powerful ideas: a simple but effective "
        "memory MCP that proved the value of persistent context, and the agentic coding philosophy "
        "from a veteran developer with 15+ years of experience.",
        styles['OCBody']
    ))

    elements.append(Spacer(1, 15))

    # Inspiration 1
    elements.append(Paragraph("Inspiration 1: The Simple Memory Pattern", styles['OCSubSection']))
    elements.append(Paragraph(
        "A straightforward MCP that did one thing well: let Claude remember things between sessions. "
        "Simple JSON storage, basic remember/recall commands. It proved that even minimal persistence "
        "dramatically improves AI assistant effectiveness.",
        styles['OCBody']
    ))

    elements.append(Paragraph("<b>What OmniCortex took from this:</b>", styles['OCBody']))
    elements.append(Paragraph("• The core remember/recall pattern", styles['OCBulletItem']))
    elements.append(Paragraph("• Per-project storage isolation", styles['OCBulletItem']))
    elements.append(Paragraph("• Simple, intuitive tool naming", styles['OCBulletItem']))

    elements.append(Paragraph("<b>What OmniCortex added:</b>", styles['OCBody']))
    elements.append(Paragraph("• Full-text search with ranking", styles['OCBulletItem']))
    elements.append(Paragraph("• Memory types and auto-categorization", styles['OCBulletItem']))
    elements.append(Paragraph("• Cross-project global index", styles['OCBulletItem']))
    elements.append(Paragraph("• Semantic (AI-powered) search", styles['OCBulletItem']))

    elements.append(Spacer(1, 20))

    # Inspiration 2
    elements.append(Paragraph("Inspiration 2: The Agentic Coding Philosophy", styles['OCSubSection']))
    elements.append(Paragraph(
        "A framework from a veteran developer that shifts thinking from \"AI writes code\" to "
        "\"AI builds systems that build systems.\" Key principles:",
        styles['OCBody']
    ))

    elements.append(create_callout_box(
        '"Store everything important - decisions, failures, solutions"',
        SECONDARY
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Core philosophy adopted:</b>", styles['OCBody']))
    elements.append(Paragraph("• Never repeat the same mistake twice", styles['OCBulletItem']))
    elements.append(Paragraph("• Context preservation across sessions", styles['OCBulletItem']))
    elements.append(Paragraph("• Audit trail for debugging and learning", styles['OCBulletItem']))
    elements.append(Paragraph("• System-level thinking over task-level thinking", styles['OCBulletItem']))

    elements.append(Paragraph("<b>What OmniCortex built from this:</b>", styles['OCBody']))
    elements.append(Paragraph("• Activity logging (complete audit trail)", styles['OCBulletItem']))
    elements.append(Paragraph("• Session management with summaries", styles['OCBulletItem']))
    elements.append(Paragraph("• Key learnings capture at session end", styles['OCBulletItem']))
    elements.append(Paragraph("• Timeline view for understanding history", styles['OCBulletItem']))

    # Page 2
    elements.append(PageBreak())
    elements.append(Paragraph("Design Principles", styles['OCSectionTitle']))

    principles = [
        ("Zero Configuration", "Works out of the box. Install, run setup, restart. "
         "No manual JSON editing required."),
        ("Dual-Layer Storage", "Activity log for the audit trail (what happened), "
         "knowledge store for insights (what was learned)."),
        ("Progressive Enhancement", "Start with keyword search. Add semantic search later. "
         "Everything works without optional features."),
        ("Project Isolation", "Each project has its own database. Global index enables "
         "cross-project discovery without mixing data."),
        ("Smart Defaults", "Auto-categorize, auto-tag, auto-rank. The system learns "
         "which memories matter most."),
    ]

    for title, desc in principles:
        box_data = [[
            Paragraph(f"<b>{title}</b>", ParagraphStyle('PTitle',
                fontName='Helvetica-Bold', fontSize=11, textColor=PRIMARY)),
            Paragraph(desc, ParagraphStyle('PDesc',
                fontName='Helvetica', fontSize=10, textColor=TEXT_DARK, leading=13))
        ]]
        box = Table(box_data, colWidths=[1.8*inch, 3.7*inch])
        box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(box)
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph("The Result", styles['OCSectionTitle']))
    elements.append(Paragraph(
        "OmniCortex combines the simplicity of basic memory storage with the sophistication of "
        "enterprise-grade context management. It's designed for developers who want their AI "
        "assistant to truly learn and remember - not just within a session, but across their "
        "entire development journey.",
        styles['OCBody']
    ))

    elements.append(Spacer(1, 15))
    elements.append(create_callout_box(
        "18 tools • 11 memory types • Activity logging • Session continuity • Global search",
        ACCENT
    ))

    # Build PDF
    doc.build(elements, onFirstPage=lambda c, d: header_footer(c, d, "Philosophy & Design"),
              onLaterPages=lambda c, d: header_footer(c, d, "Philosophy & Design"))
    print("Created: OmniCortex_Philosophy.pdf")


# === DOCUMENT 4: COMMAND REFERENCE ===
def create_command_reference_pdf():
    """Create the Command Reference PDF."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_CommandReference.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=60, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    elements.append(Paragraph("OmniCortex Command Reference", styles['OCDocTitle']))
    elements.append(Paragraph("Complete Tool Guide", styles['OCDocSubtitle']))

    # Memory Tools
    elements.append(Paragraph("Memory Tools (6)", styles['OCSectionTitle']))

    memory_cmds = [
        ('cortex_remember', 'Store information', 'content, context, tags, type, importance'),
        ('cortex_recall', 'Search memories', 'query, search_mode, type_filter, limit'),
        ('cortex_list_memories', 'List all memories', 'type_filter, sort_by, limit, offset'),
        ('cortex_update_memory', 'Update a memory', 'id, content, add_tags, status'),
        ('cortex_forget', 'Delete a memory', 'id, confirm=true'),
        ('cortex_link_memories', 'Link two memories', 'source_id, target_id, relationship_type'),
    ]

    for cmd, desc, params in memory_cmds:
        elements.append(Paragraph(f"<font name='Courier' color='#2563EB'>{cmd}</font>", styles['OCBody']))
        elements.append(Paragraph(f"{desc}. Params: <i>{params}</i>",
            ParagraphStyle('CmdDesc', fontSize=9, textColor=TEXT_MUTED, leftIndent=20, spaceAfter=8)))

    # Activity Tools
    elements.append(Paragraph("Activity Tools (3)", styles['OCSectionTitle']))

    activity_cmds = [
        ('cortex_log_activity', 'Log manual activity', 'event_type, tool_name, success'),
        ('cortex_get_activities', 'Query activity log', 'session_id, tool_name, since, limit'),
        ('cortex_get_timeline', 'Chronological view', 'hours, include_activities, group_by'),
    ]

    for cmd, desc, params in activity_cmds:
        elements.append(Paragraph(f"<font name='Courier' color='#7C3AED'>{cmd}</font>", styles['OCBody']))
        elements.append(Paragraph(f"{desc}. Params: <i>{params}</i>",
            ParagraphStyle('CmdDesc', fontSize=9, textColor=TEXT_MUTED, leftIndent=20, spaceAfter=8)))

    # Session Tools
    elements.append(Paragraph("Session Tools (3)", styles['OCSectionTitle']))

    session_cmds = [
        ('cortex_start_session', 'Start work session', 'provide_context, context_depth'),
        ('cortex_end_session', 'End session with summary', 'session_id, summary, key_learnings'),
        ('cortex_get_session_context', 'Get previous context', 'session_count, include_decisions'),
    ]

    for cmd, desc, params in session_cmds:
        elements.append(Paragraph(f"<font name='Courier' color='#10B981'>{cmd}</font>", styles['OCBody']))
        elements.append(Paragraph(f"{desc}. Params: <i>{params}</i>",
            ParagraphStyle('CmdDesc', fontSize=9, textColor=TEXT_MUTED, leftIndent=20, spaceAfter=8)))

    # Utility & Global Tools
    elements.append(Paragraph("Utility & Global Tools (6)", styles['OCSectionTitle']))

    utility_cmds = [
        ('cortex_list_tags', 'List all tags', 'min_count, limit'),
        ('cortex_review_memories', 'Review freshness', 'action, days_threshold, memory_ids'),
        ('cortex_export', 'Export data', 'format (markdown/json/sqlite), output_path'),
        ('cortex_global_search', 'Cross-project search', 'query, project_filter, limit'),
        ('cortex_global_stats', 'Global statistics', '(no parameters)'),
        ('cortex_sync_to_global', 'Sync to global index', 'full_sync'),
    ]

    for cmd, desc, params in utility_cmds:
        elements.append(Paragraph(f"<font name='Courier' color='#F59E0B'>{cmd}</font>", styles['OCBody']))
        elements.append(Paragraph(f"{desc}. Params: <i>{params}</i>",
            ParagraphStyle('CmdDesc', fontSize=9, textColor=TEXT_MUTED, leftIndent=20, spaceAfter=8)))

    # Page 2: Memory Types & Search Modes
    elements.append(PageBreak())

    elements.append(Paragraph("Memory Types", styles['OCSectionTitle']))
    types_data = [
        ['Type', 'Auto-detected When...'],
        ['solution', 'Contains "fix", "resolved", "solution"'],
        ['warning', 'Contains "warning", "avoid", "never"'],
        ['config', 'Contains "config", "setting", "environment"'],
        ['troubleshooting', 'Contains "debug", "troubleshoot"'],
        ['code', 'Contains "function", "class", "algorithm"'],
        ['error', 'Contains "error", "exception", "failed"'],
        ['command', 'Contains "run", "execute", "command"'],
        ['concept', 'Contains "what is", "definition"'],
        ['decision', 'Contains "decided", "chose", "architecture"'],
        ['tip', 'Contains "tip", "trick", "best practice"'],
        ['general', 'Default type'],
    ]
    types_table = Table(types_data, colWidths=[1.5*inch, 4*inch])
    types_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(types_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Search Modes", styles['OCSectionTitle']))
    search_data = [
        ['Mode', 'Engine', 'Best For'],
        ['keyword', 'SQLite FTS5 + BM25', 'Exact terms, specific phrases'],
        ['semantic', 'sentence-transformers', 'Conceptual similarity, natural language'],
        ['hybrid', 'FTS5 + embeddings', 'Best overall results (recommended)'],
    ]
    search_table = Table(search_data, colWidths=[1.2*inch, 2*inch, 2.3*inch])
    search_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(search_table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "<i>Note: Semantic search requires pip install omni-cortex[semantic]</i>",
        ParagraphStyle('Note', fontSize=9, textColor=TEXT_MUTED)
    ))

    # Build PDF
    doc.build(elements, onFirstPage=lambda c, d: header_footer(c, d, "Command Reference"),
              onLaterPages=lambda c, d: header_footer(c, d, "Command Reference"))
    print("Created: OmniCortex_CommandReference.pdf")


if __name__ == "__main__":
    print("Creating OmniCortex Teaching Materials...")
    create_quickstart_pdf()
    create_comparison_pdf()
    create_philosophy_pdf()
    create_command_reference_pdf()
    print("\nAll PDFs created successfully!")
