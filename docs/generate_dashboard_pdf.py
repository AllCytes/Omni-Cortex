"""Generate OmniCortex Dashboard Guide PDF with updated Ask AI section."""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Colors matching existing style
PRIMARY = colors.HexColor('#4A90D9')  # Blue
ACCENT = colors.HexColor('#2ECC71')   # Green
TEXT = colors.HexColor('#333333')
LIGHT_BG = colors.HexColor('#E8F4F8')
CODE_BG = colors.HexColor('#2ECC71')
WARNING_BG = colors.HexColor('#FFF3CD')
WARNING_TEXT = colors.HexColor('#856404')


def header_footer(canvas, doc):
    """Add header and footer to each page."""
    canvas.saveState()
    # Header
    canvas.setFillColor(PRIMARY)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(72, 756, "Dashboard User Guide")
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


def create_warning_box(text):
    """Create a warning/setup required box."""
    data = [[Paragraph(text, ParagraphStyle('Warning',
        fontName='Helvetica-Bold', fontSize=10, textColor=WARNING_TEXT,
        leading=14))]]
    table = Table(data, colWidths=[5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WARNING_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    return table


def create_two_column_box(left_title, left_items, right_title, right_items):
    """Create a two-column feature box."""
    left_content = f"<b>{left_title}</b><br/>" + "<br/>".join([f"&bull; {item}" for item in left_items])
    right_content = f"<b>{right_title}</b><br/>" + "<br/>".join([f"&bull; {item}" for item in right_items])

    left_para = Paragraph(left_content, ParagraphStyle('BoxLeft',
        fontName='Helvetica', fontSize=10, textColor=TEXT, leading=14))
    right_para = Paragraph(right_content, ParagraphStyle('BoxRight',
        fontName='Helvetica', fontSize=10, textColor=TEXT, leading=14))

    data = [[left_para, right_para]]
    table = Table(data, colWidths=[2.75*inch, 2.75*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return table


def build_pdf():
    doc = SimpleDocTemplate(
        "OmniCortex_DashboardGuide.pdf",
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
    subheading_style = ParagraphStyle('Subheading',
        fontName='Helvetica-Bold', fontSize=12, textColor=PRIMARY,
        spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('Body',
        fontName='Helvetica', fontSize=11, textColor=TEXT,
        leading=16, spaceAfter=10)
    bullet_style = ParagraphStyle('Bullet',
        fontName='Helvetica', fontSize=10, textColor=TEXT,
        leading=14, leftIndent=20, bulletIndent=10, spaceAfter=4)

    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Web Dashboard", title_style))
    elements.append(Paragraph("User Guide", subtitle_style))
    elements.append(Paragraph(
        "The OmniCortex Dashboard is a visual interface for browsing, searching, and managing your "
        "memories. Built with Vue 3 and FastAPI, it provides real-time updates and powerful analytics.",
        body_style
    ))

    # Quick Start
    elements.append(Paragraph("Quick Start", heading_style))
    elements.append(create_code_block("omni-cortex-dashboard<br/>Opens at http://localhost:8765"))
    elements.append(Spacer(1, 10))

    # Key Features
    elements.append(Paragraph("Key Features", heading_style))
    elements.append(create_two_column_box(
        "Core Features",
        ["6 Feature Tabs", "Real-time WebSocket updates", "Project switching", "Dark/Light theme support"],
        "Data Management",
        ["Export to JSON, Markdown, CSV", "Bulk status updates", "Memory editing & deletion", "Advanced filtering"]
    ))
    elements.append(Spacer(1, 10))

    # Dashboard Tabs Overview
    elements.append(Paragraph("Dashboard Tabs Overview", heading_style))
    tabs_data = [
        ['Tab', 'Icon', 'Purpose'],
        ['Memories', 'Database', 'Browse, search, filter, and edit memories'],
        ['Activity', 'History', 'View complete audit trail of tool usage'],
        ['Statistics', 'BarChart', 'Analytics: heatmaps, charts, distributions'],
        ['Review', 'RefreshCw', 'Mark stale memories as fresh/outdated/archived'],
        ['Graph', 'Network', 'Visualize memory relationships with D3.js'],
        ['Ask AI', 'MessageSquare', 'Natural language queries (requires Gemini API)'],
    ]
    tabs_table = Table(tabs_data, colWidths=[1.2*inch, 1.2*inch, 3*inch])
    tabs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tabs_table)

    # PAGE BREAK
    elements.append(PageBreak())

    # Memories Tab
    elements.append(Paragraph("Memories Tab", heading_style))
    elements.append(Paragraph(
        "The Memory Browser is the primary interface for viewing and managing your stored knowledge.",
        body_style
    ))
    elements.append(Paragraph("&bull; <b>Infinite Scroll</b> - Loads 50+ memories at a time as you scroll", bullet_style))
    elements.append(Paragraph("&bull; <b>Advanced Filtering</b> - Filter by type, status, tags, importance range", bullet_style))
    elements.append(Paragraph("&bull; <b>Sorting Options</b> - Sort by last accessed, created date, importance, access count", bullet_style))
    elements.append(Paragraph("&bull; <b>Full-text Search</b> - Search in content and context with highlighting", bullet_style))
    elements.append(Paragraph("&bull; <b>Detail Panel</b> - Right sidebar shows full memory with edit/delete options", bullet_style))
    elements.append(Paragraph("&bull; <b>Export Options</b> - Copy as Markdown or download as JSON", bullet_style))

    # Activity Tab
    elements.append(Paragraph("Activity Tab", heading_style))
    elements.append(Paragraph(
        "Complete audit trail of every tool call made during your sessions.",
        body_style
    ))
    elements.append(Paragraph("&bull; <b>Event Type Filter</b> - pre_tool_use, post_tool_use, decision, observation", bullet_style))
    elements.append(Paragraph("&bull; <b>Tool Filter</b> - Filter by specific tool name", bullet_style))
    elements.append(Paragraph("&bull; <b>Status Indicators</b> - Success/failure badges with error messages", bullet_style))
    elements.append(Paragraph("&bull; <b>Timing Info</b> - Duration in ms/seconds, exact timestamps", bullet_style))
    elements.append(Paragraph("&bull; <b>Date Grouping</b> - Activities grouped chronologically by date", bullet_style))
    elements.append(create_code_block("Activity Stats: Total activities | Success count | Failed count"))

    # Statistics Tab
    elements.append(Paragraph("Statistics Tab", heading_style))
    elements.append(Paragraph(
        "Comprehensive analytics and visualizations for your memory data.",
        body_style
    ))
    stats_data = [
        ['Chart', 'Description'],
        ['Overview Cards', 'Total memories, average importance, total views'],
        ['Type Distribution', 'Horizontal bar chart showing memories per type'],
        ['Status Distribution', 'Progress bars for fresh/needs_review/outdated/archived'],
        ['Top Tags', 'Top 15 tags with usage counts (clickable)'],
        ['Activity Heatmap', '90-day GitHub-style calendar visualization'],
        ['Tool Usage Chart', 'Top 10 tools with success rate indicators'],
        ['Memory Growth', '30-day line chart: cumulative + daily new'],
    ]
    stats_table = Table(stats_data, colWidths=[1.8*inch, 3.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(stats_table)

    # PAGE BREAK
    elements.append(PageBreak())

    # Review Tab
    elements.append(Paragraph("Review Tab (Freshness Management)", heading_style))
    elements.append(Paragraph(
        "Keep your knowledge base fresh by reviewing stale memories.",
        body_style
    ))
    elements.append(Paragraph("&bull; <b>Days Threshold</b> - Configure: 7, 14, 30, 60, or 90 days", bullet_style))
    elements.append(Paragraph("&bull; <b>Bulk Selection</b> - Select all or individual memories", bullet_style))
    elements.append(Paragraph("&bull; <b>Batch Actions</b> - Mark Fresh | Mark Outdated | Archive", bullet_style))
    elements.append(Paragraph("&bull; <b>Progress Bar</b> - Shows review completion percentage", bullet_style))

    # Relationship Graph Tab
    elements.append(Paragraph("Relationship Graph Tab", heading_style))
    elements.append(Paragraph(
        "Interactive D3.js force-directed network visualization of memory connections.",
        body_style
    ))
    elements.append(create_two_column_box(
        "Node Features",
        ["Color-coded by memory type", "Drag to reposition", "Click to select", "Double-click to recenter"],
        "Edge Types",
        ["related_to (solid)", "supersedes (dashed, amber)", "derived_from (dotted, purple)", "contradicts (dotted, red)"]
    ))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("&bull; <b>Zoom Controls:</b> In, out, reset with percentage display", bullet_style))
    elements.append(Paragraph("&bull; <b>Legend Panel:</b> Shows all node types and edge types", bullet_style))
    elements.append(Paragraph("&bull; <b>Info Panel:</b> Selected memory content preview at bottom", bullet_style))

    # Ask AI Tab (UPDATED SECTION)
    elements.append(Paragraph("Ask AI Tab", heading_style))
    elements.append(Paragraph(
        "Natural language queries about your memories using Gemini.",
        body_style
    ))
    elements.append(create_warning_box("Setup Required: export GEMINI_API_KEY=your_api_key_here"))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("&bull; <b>Conversational Interface</b> - Multi-turn conversation history", bullet_style))
    elements.append(Paragraph("&bull; <b>Source Citations</b> - Responses cite which memories were used", bullet_style))
    elements.append(Paragraph("&bull; <b>Clickable Sources</b> - Click citations to navigate to memory", bullet_style))
    elements.append(Paragraph("&bull; <b>Example Prompts</b> - Suggested queries to get started", bullet_style))

    # NEW: Chat UX Features (v1.0.11)
    elements.append(Paragraph("Chat UX Features (v1.0.11+)", subheading_style))
    chat_features_data = [
        ['Feature', 'Description'],
        ['Thinking Indicator', 'Shows "Thinking (Xs)" with real-time elapsed counter'],
        ['Cancel Button', 'X button to abort long-running queries'],
        ['Copy Message', 'Hover over assistant messages to copy (shows checkmark)'],
        ['Regenerate', 'Refresh icon on last response to retry with same question'],
        ['Edit Message', 'Pencil icon on user messages to edit and resend'],
    ]
    chat_table = Table(chat_features_data, colWidths=[1.5*inch, 4*inch])
    chat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(chat_table)
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(
        "<b>Tip:</b> Use Ctrl+Enter to submit edited messages. Action buttons appear on hover.",
        ParagraphStyle('Tip', fontName='Helvetica-Oblique', fontSize=10, textColor=TEXT)
    ))

    # PAGE BREAK
    elements.append(PageBreak())

    # Header Navigation
    elements.append(Paragraph("Header Navigation", heading_style))
    header_data = [
        ['Element', 'Function'],
        ['Project Switcher', 'Switch between projects; click Manage for full control'],
        ['Search Bar', 'Full-text search (Enter to search, Esc to clear)'],
        ['Refresh Button', 'Reload data with loading spinner'],
        ['Export Button', 'Export to JSON, Markdown, or CSV'],
        ['Filter Toggle', 'Show/hide the filter panel'],
        ['Theme Switcher', 'Light, Dark, or System preference'],
        ['Help Button', 'Open help modal with shortcuts and tour replay'],
        ['Connection Status', 'Live indicator with auto-updating timer (pulsing dot)'],
    ]
    header_table = Table(header_data, colWidths=[1.6*inch, 3.8*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_table)

    # Project Management
    elements.append(Paragraph("Project Management", heading_style))
    elements.append(Paragraph(
        "The Dashboard includes a comprehensive Project Management system accessible via the "
        "<b>Manage</b> button in the Project Switcher dropdown.",
        body_style
    ))

    elements.append(Paragraph("Opening Project Management", subheading_style))
    elements.append(Paragraph("1. Click on the current project name in the header to open the Project Switcher dropdown", bullet_style))
    elements.append(Paragraph("2. Click the <b>Manage</b> button (gear icon) in the top-right corner of the dropdown", bullet_style))
    elements.append(Paragraph("3. The Project Management modal will open with three tabs", bullet_style))

    elements.append(Paragraph("Projects Tab", subheading_style))
    elements.append(Paragraph("&bull; <b>Favorites Section</b> - Shows starred projects at the top for quick access", bullet_style))
    elements.append(Paragraph("&bull; <b>All Projects</b> - Complete list of discovered and registered projects", bullet_style))
    elements.append(Paragraph("&bull; <b>Star Icon</b> - Click to add/remove a project from favorites", bullet_style))
    elements.append(Paragraph("&bull; <b>Trash Icon</b> - Click to unregister manually-added projects", bullet_style))
    elements.append(Paragraph('&bull; <b>Badges</b> - Projects show "(registered)" for manually added, "(global)" for global database', bullet_style))

    elements.append(Paragraph("Directories Tab", subheading_style))
    elements.append(Paragraph(
        "Configure which directories are automatically scanned for OmniCortex projects:",
        body_style
    ))
    elements.append(Paragraph("&bull; <b>Add Directory</b> - Enter a path (e.g., ~/my-projects or D:/Work) and click Add", bullet_style))
    elements.append(Paragraph("&bull; <b>Remove Directory</b> - Click the trash icon next to any directory", bullet_style))
    elements.append(Paragraph("&bull; <b>Default directories</b> - System auto-detects ~/Projects, ~/code, ~/dev, etc.", bullet_style))

    elements.append(Paragraph("Add Project Tab", subheading_style))
    elements.append(Paragraph("Manually register projects from any location:", body_style))
    elements.append(Paragraph("&bull; <b>Project Path</b> (required) - Full path to the project directory", bullet_style))
    elements.append(Paragraph("&bull; <b>Display Name</b> (optional) - Custom name to show in the project list", bullet_style))
    elements.append(Paragraph("&bull; <b>Requirements</b> - Path must contain .omni-cortex/cortex.db file", bullet_style))
    elements.append(Paragraph("&bull; Registered projects appear in the list even if not in scan directories", bullet_style))
    elements.append(Spacer(1, 5))
    elements.append(create_code_block(
        "Configuration Storage: ~/.omni-cortex/projects.json<br/>"
        "Stores: scan directories, registered projects, favorites, recent (last 10)"
    ))

    # PAGE BREAK
    elements.append(PageBreak())

    # Keyboard Shortcuts
    elements.append(Paragraph("Keyboard Shortcuts", heading_style))
    shortcuts_data = [
        ['Shortcut', 'Action'],
        ['/', 'Focus search bar'],
        ['Esc', 'Clear selection/filters'],
        ['j / k', 'Navigate down/up through memories'],
        ['Enter', 'Select first memory / Submit chat'],
        ['r', 'Refresh data'],
        ['?', 'Open Help dialog'],
        ['1-9', 'Quick filter by memory type'],
    ]
    shortcuts_table = Table(shortcuts_data, colWidths=[1.5*inch, 4*inch])
    shortcuts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(shortcuts_table)

    # Pro Tips
    elements.append(Paragraph("Pro Tips", heading_style))
    elements.append(Paragraph("&bull; First-time users see an <b>onboarding tour</b> - replay it via Help button", bullet_style))
    elements.append(Paragraph("&bull; Use the <b>Activity Heatmap</b> to identify your most productive periods", bullet_style))
    elements.append(Paragraph("&bull; Link related memories to build a knowledge graph for visualization", bullet_style))
    elements.append(Paragraph("&bull; Review stale memories monthly to keep your knowledge base fresh", bullet_style))
    elements.append(Paragraph("&bull; Use <b>semantic search</b> for conceptual queries (requires omni-cortex[semantic])", bullet_style))
    elements.append(Paragraph("&bull; Export memories before major refactoring for backup", bullet_style))
    elements.append(Paragraph("&bull; <b>Star your most-used projects</b> for quick access in the Project Switcher", bullet_style))
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
    print("Generated: OmniCortex_DashboardGuide.pdf")


if __name__ == "__main__":
    build_pdf()
