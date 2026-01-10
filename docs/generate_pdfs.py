"""Generate updated OmniCortex PDF documentation."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Color scheme matching existing PDFs
PRIMARY_BLUE = colors.HexColor('#4A7AFF')
ACCENT_BLUE = colors.HexColor('#5B8DEF')
HEADER_BG = colors.HexColor('#4A7AFF')
GREEN_ACCENT = colors.HexColor('#22C997')
LIGHT_GRAY = colors.HexColor('#F5F5F5')
TEXT_DARK = colors.HexColor('#333333')
TEXT_GRAY = colors.HexColor('#666666')


def create_styles():
    """Create consistent styles for all PDFs."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=PRIMARY_BLUE,
        spaceAfter=6,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        textColor=TEXT_GRAY,
        spaceAfter=20,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=PRIMARY_BLUE,
        spaceBefore=20,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        'SubHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=PRIMARY_BLUE,
        spaceBefore=15,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        'OmniBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=TEXT_DARK,
        leading=16,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        'BulletItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=TEXT_DARK,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=10,
        textColor=TEXT_DARK,
        backColor=LIGHT_GRAY,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=5
    ))

    return styles


def header_footer(canvas, doc, title="Dashboard User Guide"):
    """Add header and footer to each page."""
    canvas.saveState()

    # Header text
    canvas.setFillColor(PRIMARY_BLUE)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(50, 756, title)

    # Header line
    canvas.setStrokeColor(PRIMARY_BLUE)
    canvas.setLineWidth(2)
    canvas.line(50, 748, 562, 748)

    # Footer line
    canvas.setStrokeColor(LIGHT_GRAY)
    canvas.setLineWidth(1)
    canvas.line(50, 40, 562, 40)

    # Page number
    canvas.setFillColor(TEXT_GRAY)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(306, 25, f"Page {doc.page}")

    canvas.restoreState()


def create_table(data, col_widths=None, header_bg=HEADER_BG):
    """Create a styled table."""
    if col_widths is None:
        col_widths = [1.5*inch] * len(data[0])

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
    ]))
    return table


def create_callout_box(text, bg_color=GREEN_ACCENT):
    """Create a colored callout box."""
    style = ParagraphStyle(
        'Callout',
        fontName='Courier',
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER
    )
    data = [[Paragraph(text, style)]]
    table = Table(data, colWidths=[5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    return table


def create_two_column_box(left_title, left_items, right_title, right_items):
    """Create a two-column feature box."""
    left_style = ParagraphStyle('LeftCol', fontName='Helvetica-Bold', fontSize=12,
                                 textColor=PRIMARY_BLUE, spaceAfter=6)
    right_style = ParagraphStyle('RightCol', fontName='Helvetica-Bold', fontSize=12,
                                  textColor=PRIMARY_BLUE, spaceAfter=6)
    item_style = ParagraphStyle('Item', fontName='Helvetica', fontSize=10,
                                 textColor=TEXT_DARK, leftIndent=10)

    left_content = [Paragraph(left_title, left_style)]
    for item in left_items:
        left_content.append(Paragraph(f"• {item}", item_style))

    right_content = [Paragraph(right_title, right_style)]
    for item in right_items:
        right_content.append(Paragraph(f"• {item}", item_style))

    left_table = Table([[p] for p in left_content], colWidths=[2.8*inch])
    right_table = Table([[p] for p in right_content], colWidths=[2.8*inch])

    for t in [left_table, right_table]:
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ]))

    outer = Table([[left_table, right_table]], colWidths=[3*inch, 3*inch])
    outer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (0, -1), 3, PRIMARY_BLUE),
        ('BOX', (1, 0), (1, -1), 3, PRIMARY_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return outer


def generate_dashboard_guide():
    """Generate OmniCortex_DashboardGuide.pdf with Project Management section."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_DashboardGuide.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=70, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    # Title page content
    elements.append(Paragraph("OmniCortex Web Dashboard", styles['DocTitle']))
    elements.append(Paragraph("User Guide", styles['DocSubtitle']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "The OmniCortex Dashboard is a visual interface for browsing, searching, and managing your memories. "
        "Built with Vue 3 and FastAPI, it provides real-time updates and powerful analytics.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 15))

    # Quick Start
    elements.append(Paragraph("Quick Start", styles['SectionHeading']))
    elements.append(create_callout_box("omni-cortex-dashboard<br/>Opens at <b>http://localhost:8765</b>"))
    elements.append(Spacer(1, 15))

    # Key Features
    elements.append(Paragraph("Key Features", styles['SectionHeading']))
    elements.append(create_two_column_box(
        "Core Features",
        ["6 Feature Tabs", "Real-time WebSocket updates", "Project switching", "Dark/Light theme support"],
        "Data Management",
        ["Export to JSON, Markdown, CSV", "Bulk status updates", "Memory editing & deletion", "Advanced filtering"]
    ))
    elements.append(Spacer(1, 15))

    # Dashboard Tabs Overview
    elements.append(Paragraph("Dashboard Tabs Overview", styles['SectionHeading']))
    tabs_data = [
        ["Tab", "Icon", "Purpose"],
        ["Memories", "Database", "Browse, search, filter, and edit memories"],
        ["Activity", "History", "View complete audit trail of tool usage"],
        ["Statistics", "BarChart", "Analytics: heatmaps, charts, distributions"],
        ["Review", "RefreshCw", "Mark stale memories as fresh/outdated/archived"],
        ["Graph", "Network", "Visualize memory relationships with D3.js"],
        ["Ask AI", "MessageSquare", "Natural language queries (requires Gemini API)"],
    ]
    elements.append(create_table(tabs_data, [1.2*inch, 1.2*inch, 3.6*inch]))
    elements.append(PageBreak())

    # Memories Tab
    elements.append(Paragraph("Memories Tab", styles['SectionHeading']))
    elements.append(Paragraph(
        "The Memory Browser is the primary interface for viewing and managing your stored knowledge.",
        styles['OmniBody']
    ))
    for item in [
        "<b>Infinite Scroll</b> - Loads 50+ memories at a time as you scroll",
        "<b>Advanced Filtering</b> - Filter by type, status, tags, importance range",
        "<b>Sorting Options</b> - Sort by last accessed, created date, importance, access count",
        "<b>Full-text Search</b> - Search in content and context with highlighting",
        "<b>Detail Panel</b> - Right sidebar shows full memory with edit/delete options",
        "<b>Export Options</b> - Copy as Markdown or download as JSON"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 15))

    # Activity Tab
    elements.append(Paragraph("Activity Tab", styles['SectionHeading']))
    elements.append(Paragraph(
        "Complete audit trail of every tool call made during your sessions.",
        styles['OmniBody']
    ))
    for item in [
        "<b>Event Type Filter</b> - pre_tool_use, post_tool_use, decision, observation",
        "<b>Tool Filter</b> - Filter by specific tool name",
        "<b>Status Indicators</b> - Success/failure badges with error messages",
        "<b>Timing Info</b> - Duration in ms/seconds, exact timestamps",
        "<b>Date Grouping</b> - Activities grouped chronologically by date",
        "<b>Expandable Rows</b> - Click to view full JSON input/output with copy button",
        "<b>MCP Badges</b> - Shows which MCP server handled the tool call",
        "<b>Command/Skill Tags</b> - Visual badges for slash commands and skills"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 10))
    elements.append(create_callout_box(
        "<b>Activity Stats:</b> Total activities | Success count | Failed count",
        colors.HexColor('#EF7B45')
    ))
    elements.append(PageBreak())

    # Statistics Tab
    elements.append(Paragraph("Statistics Tab", styles['SectionHeading']))
    elements.append(Paragraph(
        "Comprehensive analytics and visualizations for your memory data.",
        styles['OmniBody']
    ))
    stats_data = [
        ["Chart", "Description"],
        ["Overview Cards", "Total memories, average importance, total views"],
        ["Type Distribution", "Horizontal bar chart showing memories per type"],
        ["Status Distribution", "Progress bars for fresh/needs_review/outdated/archived"],
        ["Top Tags", "Top 15 tags with usage counts (clickable)"],
        ["Activity Heatmap", "90-day GitHub-style calendar visualization"],
        ["Tool Usage Chart", "Top 10 tools with success rate indicators"],
        ["Memory Growth", "30-day line chart: cumulative + daily new"],
    ]
    elements.append(create_table(stats_data, [2*inch, 4*inch]))
    elements.append(Spacer(1, 15))

    # Command & Skill Analytics (NEW - v1.3.0)
    elements.append(Paragraph("Command & Skill Analytics (v1.3.0+)", styles['SubHeading']))
    elements.append(Paragraph(
        "Track slash command and skill usage patterns with scope differentiation.",
        styles['OmniBody']
    ))
    analytics_data = [
        ["Chart", "Description"],
        ["Command Usage", "Bar chart: slash commands by usage count, filterable by scope (universal/project)"],
        ["Skill Usage", "Bar chart: skill adoption and success rates"],
        ["MCP Usage", "Doughnut chart: MCP server integration metrics with tool/call counts"],
    ]
    elements.append(create_table(analytics_data, [2*inch, 4*inch]))
    elements.append(Spacer(1, 20))

    # Review Tab
    elements.append(Paragraph("Review Tab (Freshness Management)", styles['SectionHeading']))
    elements.append(Paragraph(
        "Keep your knowledge base fresh by reviewing stale memories.",
        styles['OmniBody']
    ))
    for item in [
        "<b>Days Threshold</b> - Configure: 7, 14, 30, 60, or 90 days",
        "<b>Bulk Selection</b> - Select all or individual memories",
        "<b>Batch Actions</b> - Mark Fresh | Mark Outdated | Archive",
        "<b>Progress Bar</b> - Shows review completion percentage"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(PageBreak())

    # Relationship Graph Tab
    elements.append(Paragraph("Relationship Graph Tab", styles['SectionHeading']))
    elements.append(Paragraph(
        "Interactive D3.js force-directed network visualization of memory connections.",
        styles['OmniBody']
    ))
    elements.append(create_two_column_box(
        "Node Features",
        ["Color-coded by memory type", "Drag to reposition", "Click to select", "Double-click to recenter"],
        "Edge Types",
        ["related_to (solid)", "supersedes (dashed, amber)", "derived_from (dotted, purple)", "contradicts (dotted, red)"]
    ))
    elements.append(Spacer(1, 10))
    for item in [
        "<b>Zoom Controls:</b> In, out, reset with percentage display",
        "<b>Legend Panel:</b> Shows all node types and edge types",
        "<b>Info Panel:</b> Selected memory content preview at bottom"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 15))

    # Ask AI Tab
    elements.append(Paragraph("Ask AI Tab", styles['SectionHeading']))
    elements.append(Paragraph(
        "Natural language queries about your memories using Gemini.",
        styles['OmniBody']
    ))
    elements.append(create_callout_box(
        "<b>Setup Required:</b> export GEMINI_API_KEY=your_api_key_here",
        colors.HexColor('#EF7B45')
    ))
    elements.append(Spacer(1, 10))
    for item in [
        "<b>Conversational Interface</b> - Multi-turn conversation history",
        "<b>Source Citations</b> - Responses cite which memories were used",
        "<b>Clickable Sources</b> - Click citations to navigate to memory",
        "<b>Example Prompts</b> - Suggested queries to get started"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 15))

    # Image Generation Mode (NEW - v1.2.0)
    elements.append(Paragraph("Image Generation Mode (Nano Banana Pro)", styles['SectionHeading']))
    elements.append(Paragraph(
        "Generate visual content from your memories using Gemini 3 Pro image generation. "
        "Toggle between Chat and Generate modes in the Ask AI panel header.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))
    elements.append(create_two_column_box(
        "Image Features",
        ["8 preset templates", "Batch generation (1-4 images)", "10 aspect ratios", "1K/2K/4K resolution"],
        "Memory Integration",
        ["Select memories as context", "Search and filter memories", "Multi-turn refinement", "Click-to-edit images"]
    ))
    elements.append(Spacer(1, 10))
    preset_data = [
        ["Preset", "Best For"],
        ["Infographic", "Visual summaries with icons and data"],
        ["Key Insights", "Bullet-point style visual cards"],
        ["Tips & Tricks", "Numbered lists with visual elements"],
        ["Quote Card", "Memorable quotes styled for sharing"],
        ["Workflow", "Step-by-step process diagrams"],
        ["Comparison", "Side-by-side feature comparisons"],
        ["Summary Card", "Compact visual overviews"],
        ["Custom", "Free-form prompts with full control"],
    ]
    elements.append(create_table(preset_data, [1.8*inch, 4.2*inch]))
    elements.append(PageBreak())

    # Header Navigation
    elements.append(Paragraph("Header Navigation", styles['SectionHeading']))
    header_data = [
        ["Element", "Function"],
        ["Project Switcher", "Switch between projects; click Manage for full control"],
        ["Search Bar", "Full-text search (Enter to search, Esc to clear)"],
        ["Refresh Button", "Reload data with loading spinner"],
        ["Export Button", "Export to JSON, Markdown, or CSV"],
        ["Filter Toggle", "Show/hide the filter panel"],
        ["Theme Switcher", "Light, Dark, or System preference"],
        ["Help Button", "Open help modal with shortcuts and tour replay"],
        ["Connection Status", "Live indicator with auto-updating timer (pulsing dot)"],
    ]
    elements.append(create_table(header_data, [2*inch, 4*inch]))
    elements.append(Spacer(1, 20))

    # ========== NEW PROJECT MANAGEMENT SECTION ==========
    elements.append(Paragraph("Project Management", styles['SectionHeading']))
    elements.append(Paragraph(
        "The Dashboard includes a comprehensive Project Management system accessible via the "
        "<b>Manage</b> button in the Project Switcher dropdown.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Opening Project Management", styles['SubHeading']))
    for i, step in enumerate([
        "Click on the current project name in the header to open the Project Switcher dropdown",
        "Click the <b>Manage</b> button (gear icon) in the top-right corner of the dropdown",
        "The Project Management modal will open with three tabs"
    ], 1):
        elements.append(Paragraph(f"{i}. {step}", styles['BulletItem']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Projects Tab", styles['SubHeading']))
    for item in [
        "<b>Favorites Section</b> - Shows starred projects at the top for quick access",
        "<b>All Projects</b> - Complete list of discovered and registered projects",
        "<b>Star Icon</b> - Click to add/remove a project from favorites",
        "<b>Trash Icon</b> - Click to unregister manually-added projects",
        "<b>Badges</b> - Projects show \"(registered)\" for manually added, \"(global)\" for global database"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Directories Tab", styles['SubHeading']))
    elements.append(Paragraph(
        "Configure which directories are automatically scanned for OmniCortex projects:",
        styles['OmniBody']
    ))
    for item in [
        "<b>Add Directory</b> - Enter a path (e.g., ~/my-projects or D:/Work) and click Add",
        "<b>Remove Directory</b> - Click the trash icon next to any directory",
        "<b>Default directories</b> - System auto-detects ~/Projects, ~/code, ~/dev, etc."
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Add Project Tab", styles['SubHeading']))
    elements.append(Paragraph(
        "Manually register projects from any location:",
        styles['OmniBody']
    ))
    for item in [
        "<b>Project Path</b> (required) - Full path to the project directory",
        "<b>Display Name</b> (optional) - Custom name to show in the project list",
        "<b>Requirements</b> - Path must contain .omni-cortex/cortex.db file",
        "Registered projects appear in the list even if not in scan directories"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 10))

    elements.append(create_callout_box(
        "<b>Configuration Storage:</b> ~/.omni-cortex/projects.json<br/>"
        "Stores: scan directories, registered projects, favorites, recent (last 10)",
        PRIMARY_BLUE
    ))
    elements.append(PageBreak())

    # Keyboard Shortcuts
    elements.append(Paragraph("Keyboard Shortcuts", styles['SectionHeading']))
    shortcuts_data = [
        ["Shortcut", "Action"],
        ["/", "Focus search bar"],
        ["Esc", "Clear selection/filters"],
        ["j / k", "Navigate down/up through memories"],
        ["Enter", "Select first memory / Submit chat"],
        ["r", "Refresh data"],
        ["?", "Open Help dialog"],
        ["1-9", "Quick filter by memory type"],
    ]
    elements.append(create_table(shortcuts_data, [2*inch, 4*inch]))
    elements.append(Spacer(1, 20))

    # Pro Tips
    elements.append(Paragraph("Pro Tips", styles['SectionHeading']))
    for item in [
        "First-time users see an <b>onboarding tour</b> - replay it via Help button",
        "Use the <b>Activity Heatmap</b> to identify your most productive periods",
        "Link related memories to build a knowledge graph for visualization",
        "Review stale memories monthly to keep your knowledge base fresh",
        "Use <b>semantic search</b> for conceptual queries (requires omni-cortex[semantic])",
        "Export memories before major refactoring for backup",
        "<b>Star your most-used projects</b> for quick access in the Project Switcher"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 30))

    # Footer
    elements.append(create_callout_box(
        "<b>OmniCortex</b> | github.com/AllCytes/Omni-Cortex",
        GREEN_ACCENT
    ))

    def on_page(canvas, doc):
        header_footer(canvas, doc, "Dashboard User Guide")

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    print("Generated: OmniCortex_DashboardGuide.pdf")


def generate_storage_architecture():
    """Generate OmniCortex_StorageArchitecture.pdf with projects.json."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_StorageArchitecture.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=70, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Storage Architecture", styles['DocTitle']))
    elements.append(Paragraph("Technical Reference", styles['DocSubtitle']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "OmniCortex uses SQLite for all data storage - a deliberate architectural choice that prioritizes "
        "simplicity, portability, and reliability over distributed complexity.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 15))

    # Why SQLite?
    elements.append(Paragraph("Why SQLite?", styles['SectionHeading']))
    elements.append(create_two_column_box(
        "Technical Benefits",
        ["Zero configuration required", "Single-file databases", "ACID compliant", "Built-in FTS5 for search"],
        "Practical Benefits",
        ["Works offline", "Easy backup (copy file)", "No server process", "Cross-platform portable"]
    ))
    elements.append(Spacer(1, 15))

    # Storage Locations
    elements.append(Paragraph("Storage Locations", styles['SectionHeading']))
    storage_data = [
        ["Location", "Path", "Purpose"],
        ["Project DB", ".omni-cortex/cortex.db", "Memories, activities, sessions for project"],
        ["Global DB", "~/.omni-cortex/global.db", "Cross-project search index"],
        ["Project Config", "~/.omni-cortex/projects.json", "Dashboard settings, favorites, scan dirs"],
    ]
    elements.append(create_table(storage_data, [1.3*inch, 2.2*inch, 2.5*inch]))
    elements.append(Spacer(1, 15))

    # Database Schema
    elements.append(Paragraph("Database Schema", styles['SectionHeading']))

    elements.append(Paragraph("memories Table", styles['SubHeading']))
    memories_schema = [
        ["Column", "Type", "Description"],
        ["id", "TEXT PK", "ULID-based unique identifier"],
        ["content", "TEXT", "Main memory content"],
        ["context", "TEXT", "Additional context"],
        ["memory_type", "TEXT", "fact, decision, solution, etc."],
        ["status", "TEXT", "fresh, needs_review, outdated, archived"],
        ["importance_score", "INTEGER", "1-100 importance rating"],
        ["tags", "TEXT", "JSON array of tags"],
        ["created_at", "TIMESTAMP", "Creation time"],
        ["last_accessed", "TIMESTAMP", "Last access time"],
        ["access_count", "INTEGER", "Number of accesses"],
    ]
    elements.append(create_table(memories_schema, [1.3*inch, 1.2*inch, 3.5*inch]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("activities Table", styles['SubHeading']))
    activities_schema = [
        ["Column", "Type", "Description"],
        ["id", "TEXT PK", "ULID-based unique identifier"],
        ["event_type", "TEXT", "pre_tool_use, post_tool_use, etc."],
        ["tool_name", "TEXT", "Name of tool called"],
        ["tool_input", "TEXT", "JSON input parameters"],
        ["tool_output", "TEXT", "JSON output result"],
        ["success", "BOOLEAN", "Whether operation succeeded"],
        ["duration_ms", "INTEGER", "Execution time in ms"],
        ["session_id", "TEXT", "FK to sessions table"],
        ["timestamp", "TIMESTAMP", "Event time"],
    ]
    elements.append(create_table(activities_schema, [1.3*inch, 1.2*inch, 3.5*inch]))
    elements.append(PageBreak())

    elements.append(Paragraph("memory_relationships Table", styles['SubHeading']))
    rel_schema = [
        ["Column", "Type", "Description"],
        ["source_id", "TEXT FK", "Source memory ID"],
        ["target_id", "TEXT FK", "Target memory ID"],
        ["relationship_type", "TEXT", "related_to, supersedes, derived_from, contradicts"],
        ["strength", "REAL", "Relationship strength 0.0-1.0"],
        ["created_at", "TIMESTAMP", "When relationship was created"],
    ]
    elements.append(create_table(rel_schema, [1.5*inch, 1.2*inch, 3.3*inch]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("sessions Table", styles['SubHeading']))
    sessions_schema = [
        ["Column", "Type", "Description"],
        ["id", "TEXT PK", "Session identifier"],
        ["started_at", "TIMESTAMP", "Session start time"],
        ["ended_at", "TIMESTAMP", "Session end time (nullable)"],
        ["summary", "TEXT", "Auto-generated or manual summary"],
        ["key_learnings", "TEXT", "JSON array of learnings"],
    ]
    elements.append(create_table(sessions_schema, [1.5*inch, 1.3*inch, 3.2*inch]))
    elements.append(Spacer(1, 20))

    # Full-Text Search
    elements.append(Paragraph("Full-Text Search (FTS5)", styles['SectionHeading']))
    elements.append(Paragraph(
        "OmniCortex uses SQLite's FTS5 extension for fast full-text search across memory content and context.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))
    elements.append(create_callout_box(
        "FTS5 Index: memories_fts (content, context)<br/>"
        "Supports: phrase matching, prefix search, boolean operators",
        PRIMARY_BLUE
    ))
    elements.append(Spacer(1, 15))

    # Global Index
    elements.append(Paragraph("Global Index", styles['SectionHeading']))
    elements.append(Paragraph(
        "The global database at ~/.omni-cortex/global.db maintains a cross-project search index "
        "for finding memories across all your projects.",
        styles['OmniBody']
    ))
    global_schema = [
        ["Column", "Type", "Description"],
        ["memory_id", "TEXT", "Original memory ID"],
        ["project_path", "TEXT", "Source project path"],
        ["content", "TEXT", "Memory content (synced)"],
        ["memory_type", "TEXT", "Memory type"],
        ["tags", "TEXT", "JSON tags array"],
        ["synced_at", "TIMESTAMP", "Last sync time"],
    ]
    elements.append(create_table(global_schema, [1.3*inch, 1.2*inch, 3.5*inch]))
    elements.append(PageBreak())

    # Project Configuration (NEW)
    elements.append(Paragraph("Project Configuration", styles['SectionHeading']))
    elements.append(Paragraph(
        "Dashboard project preferences are stored in ~/.omni-cortex/projects.json:",
        styles['OmniBody']
    ))
    config_schema = [
        ["Field", "Type", "Description"],
        ["version", "integer", "Config schema version"],
        ["scan_directories", "string[]", "Directories to scan for projects"],
        ["registered_projects", "object[]", "Manually added projects with path, display_name, added_at"],
        ["favorites", "string[]", "Paths of favorite projects"],
        ["recent", "object[]", "Recently accessed projects (last 10) with path, last_accessed"],
    ]
    elements.append(create_table(config_schema, [1.8*inch, 1.2*inch, 3*inch]))
    elements.append(Spacer(1, 15))

    # Backup & Migration
    elements.append(Paragraph("Backup & Migration", styles['SectionHeading']))
    elements.append(Paragraph(
        "Because OmniCortex uses file-based storage, backup and migration are straightforward:",
        styles['OmniBody']
    ))
    for item in [
        "<b>Project Backup:</b> Copy the .omni-cortex/ directory",
        "<b>Global Backup:</b> Copy ~/.omni-cortex/ directory",
        "<b>Migration:</b> Move directories to new machine - no reconfiguration needed",
        "<b>Export:</b> Use cortex_export tool for JSON/Markdown/SQLite exports"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 30))

    # Footer
    elements.append(create_callout_box(
        "<b>OmniCortex</b> | github.com/AllCytes/Omni-Cortex",
        GREEN_ACCENT
    ))

    def on_page(canvas, doc):
        header_footer(canvas, doc, "Storage Architecture")

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    print("Generated: OmniCortex_StorageArchitecture.pdf")


def generate_quickstart():
    """Generate OmniCortex_QuickStart.pdf with projects.json."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_QuickStart.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=70, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Quick Start", styles['DocTitle']))
    elements.append(Paragraph("Get Started in 5 Minutes", styles['DocSubtitle']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "OmniCortex gives Claude persistent memory across sessions. This guide will have you "
        "up and running in minutes.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 15))

    # Installation
    elements.append(Paragraph("1. Installation", styles['SectionHeading']))
    elements.append(create_callout_box("pip install omni-cortex"))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Or with optional features:", styles['OmniBody']))
    elements.append(create_callout_box(
        "pip install omni-cortex[semantic]  # Semantic search<br/>"
        "pip install omni-cortex[all]       # All features",
        colors.HexColor('#666666')
    ))
    elements.append(Spacer(1, 15))

    # Configuration
    elements.append(Paragraph("2. Configure Claude Code", styles['SectionHeading']))
    elements.append(Paragraph(
        "Add OmniCortex to your Claude Code MCP configuration:",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("~/.claude/claude_desktop_config.json:", styles['CodeStyle']))
    elements.append(Spacer(1, 10))
    config_text = '''
{
  "mcpServers": {
    "omni-cortex": {
      "command": "omni-cortex",
      "args": ["serve"]
    }
  }
}
'''
    elements.append(Paragraph(config_text.replace('\n', '<br/>'), styles['CodeStyle']))
    elements.append(Spacer(1, 15))

    # First Use
    elements.append(Paragraph("3. First Use", styles['SectionHeading']))
    elements.append(Paragraph(
        "Start Claude Code in any project directory. OmniCortex will automatically:",
        styles['OmniBody']
    ))
    for item in [
        "Create .omni-cortex/ directory in your project",
        "Initialize cortex.db SQLite database",
        "Make memory tools available to Claude"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(PageBreak())

    # Core Tools
    elements.append(Paragraph("4. Core Tools", styles['SectionHeading']))
    tools_data = [
        ["Tool", "Purpose", "Example"],
        ["cortex_remember", "Store information", "Store this API pattern"],
        ["cortex_recall", "Search memories", "Find auth-related memories"],
        ["cortex_list_memories", "Browse all", "Show recent decisions"],
        ["cortex_update_memory", "Modify memory", "Add tags to memory"],
        ["cortex_link_memories", "Create relations", "Link related solutions"],
    ]
    elements.append(create_table(tools_data, [1.5*inch, 1.5*inch, 3*inch]))
    elements.append(Spacer(1, 15))

    # Dashboard
    elements.append(Paragraph("5. Web Dashboard", styles['SectionHeading']))
    elements.append(create_callout_box("omni-cortex-dashboard"))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "Opens a visual interface at http://localhost:8765 for browsing memories, "
        "viewing activity logs, and analyzing your knowledge base.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 15))

    # Storage Locations
    elements.append(Paragraph("6. Storage Locations", styles['SectionHeading']))
    storage_data = [
        ["Location", "Path", "Purpose"],
        ["Project DB", ".omni-cortex/cortex.db", "Project memories & activities"],
        ["Global DB", "~/.omni-cortex/global.db", "Cross-project search index"],
        ["Project Config", "~/.omni-cortex/projects.json", "Dashboard settings & favorites"],
    ]
    elements.append(create_table(storage_data, [1.3*inch, 2.2*inch, 2.5*inch]))
    elements.append(Spacer(1, 15))

    # Memory Types
    elements.append(Paragraph("7. Memory Types", styles['SectionHeading']))
    types_data = [
        ["Type", "Use For"],
        ["fact", "Technical facts, API details, configurations"],
        ["decision", "Architectural choices, design decisions"],
        ["solution", "Working fixes, implementation patterns"],
        ["error", "Error resolutions, debugging insights"],
        ["progress", "Current state, work in progress"],
        ["preference", "User preferences, coding style choices"],
    ]
    elements.append(create_table(types_data, [1.5*inch, 4.5*inch]))
    elements.append(PageBreak())

    # Tips
    elements.append(Paragraph("8. Pro Tips", styles['SectionHeading']))
    for item in [
        "Ask Claude to \"remember this\" when you solve a tricky problem",
        "Use tags liberally - they're searchable and filterable",
        "Link related memories to build a knowledge graph",
        "Review stale memories periodically (use the Review tab)",
        "Export memories before major refactoring",
        "Use the global index for cross-project patterns"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 20))

    # Next Steps
    elements.append(Paragraph("Next Steps", styles['SectionHeading']))
    elements.append(Paragraph(
        "Now that you're set up, explore these resources:",
        styles['OmniBody']
    ))
    for item in [
        "<b>Command Reference</b> - Full tool documentation",
        "<b>Dashboard Guide</b> - Visual interface walkthrough",
        "<b>Storage Architecture</b> - Technical deep dive"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 30))

    # Footer
    elements.append(create_callout_box(
        "<b>OmniCortex</b> | github.com/AllCytes/Omni-Cortex",
        GREEN_ACCENT
    ))

    def on_page(canvas, doc):
        header_footer(canvas, doc, "Quick Start Guide")

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    print("Generated: OmniCortex_QuickStart.pdf")


def generate_troubleshooting():
    """Generate OmniCortex_TroubleshootingFAQ.pdf with projects.json."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_TroubleshootingFAQ.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=70, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Troubleshooting", styles['DocTitle']))
    elements.append(Paragraph("FAQ & Common Issues", styles['DocSubtitle']))
    elements.append(Spacer(1, 10))

    # Installation Issues
    elements.append(Paragraph("Installation Issues", styles['SectionHeading']))

    elements.append(Paragraph("Q: pip install fails with dependency errors", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Try installing with the --upgrade flag to ensure latest versions:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("pip install --upgrade omni-cortex"))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Q: Command 'omni-cortex' not found after install", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Ensure your Python scripts directory is in PATH. On Windows, try:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("python -m omni_cortex serve"))
    elements.append(Spacer(1, 15))

    # Connection Issues
    elements.append(Paragraph("Connection Issues", styles['SectionHeading']))

    elements.append(Paragraph("Q: Claude can't see OmniCortex tools", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Check your MCP configuration is correct. Verify the server is running:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("omni-cortex serve --debug"))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Q: Dashboard shows 'Connection Lost'", styles['SubHeading']))
    elements.append(Paragraph(
        "A: The WebSocket connection may have timed out. Click Refresh or restart the dashboard.",
        styles['OmniBody']
    ))
    elements.append(PageBreak())

    # Data Issues
    elements.append(Paragraph("Data Issues", styles['SectionHeading']))

    elements.append(Paragraph("Q: Where is my data stored?", styles['SubHeading']))
    storage_data = [
        ["Data Type", "Location"],
        ["Project memories", ".omni-cortex/cortex.db (in project)"],
        ["Global index", "~/.omni-cortex/global.db"],
        ["Dashboard config", "~/.omni-cortex/projects.json"],
    ]
    elements.append(create_table(storage_data, [2*inch, 4*inch]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Q: How do I backup my memories?", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Simply copy the .omni-cortex directory. It's a self-contained SQLite database.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Q: Can I reset/delete all memories?", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Delete the .omni-cortex/cortex.db file. A new one will be created on next use.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 15))

    # Dashboard Issues
    elements.append(Paragraph("Dashboard Issues", styles['SectionHeading']))

    elements.append(Paragraph("Q: Dashboard won't start", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Check if port 8765 is available. Try a different port:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("omni-cortex-dashboard --port 8080"))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Q: Projects not showing in Project Switcher", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Ensure your project directories are in the scan list. Open Project Management (Manage button) "
        "and add your directory under the Directories tab, or manually register the project under Add Project.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Q: Ask AI tab shows 'API key not configured'", styles['SubHeading']))
    elements.append(Paragraph(
        "A: Set your Gemini API key as an environment variable:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("export GEMINI_API_KEY=your_api_key_here"))
    elements.append(PageBreak())

    # Performance Issues
    elements.append(Paragraph("Performance Issues", styles['SectionHeading']))

    elements.append(Paragraph("Q: Search is slow with many memories", styles['SubHeading']))
    elements.append(Paragraph(
        "A: OmniCortex uses FTS5 indexing which should handle 10,000+ memories efficiently. "
        "If you're experiencing slowness, try running VACUUM on the database.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Q: Dashboard is laggy with large datasets", styles['SubHeading']))
    elements.append(Paragraph(
        "A: The dashboard uses infinite scroll and lazy loading. Try filtering to reduce "
        "the result set, or use the search to narrow down results.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 15))

    # Getting Help
    elements.append(Paragraph("Getting Help", styles['SectionHeading']))
    elements.append(Paragraph(
        "If your issue isn't covered here:",
        styles['OmniBody']
    ))
    for item in [
        "Check the GitHub Issues for similar problems",
        "Run with --debug flag for detailed logging",
        "Open a new issue with reproduction steps"
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))
    elements.append(Spacer(1, 30))

    # Footer
    elements.append(create_callout_box(
        "<b>OmniCortex</b> | github.com/AllCytes/Omni-Cortex",
        GREEN_ACCENT
    ))

    def on_page(canvas, doc):
        header_footer(canvas, doc, "Troubleshooting FAQ")

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    print("Generated: OmniCortex_TroubleshootingFAQ.pdf")


def generate_feature_comparison():
    """Generate OmniCortex_FeatureComparison.pdf with Project Management row."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/OmniCortex_FeatureComparison.pdf",
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=70, bottomMargin=50
    )

    styles = create_styles()
    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Feature Comparison", styles['DocTitle']))
    elements.append(Paragraph("vs Basic MCP Memory", styles['DocSubtitle']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "OmniCortex provides a comprehensive memory system that goes far beyond basic MCP memory tools. "
        "Here's how they compare:",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 15))

    # Feature Comparison Table
    elements.append(Paragraph("Feature Comparison", styles['SectionHeading']))

    comparison_data = [
        ["Feature", "Basic MCP", "OmniCortex"],
        ["Memory Storage", "Simple key-value", "SQLite with full schema"],
        ["Search", "Basic lookup", "Full-text search (FTS5)"],
        ["Memory Types", "None", "7 types (fact, decision, solution, etc.)"],
        ["Status Tracking", "None", "4 statuses with freshness management"],
        ["Importance Scoring", "None", "1-100 scale with filtering"],
        ["Tagging", "None", "Multi-tag with search"],
        ["Relationships", "None", "4 relationship types with graph viz"],
        ["Activity Logging", "None", "Complete audit trail"],
        ["Session Management", "None", "Full context preservation"],
        ["Cross-Project Search", "None", "Global index"],
        ["Project Management", "None", "Favorites, custom scan dirs, registration"],
        ["Web Dashboard", "None", "Full-featured Vue 3 dashboard"],
        ["Export Options", "None", "JSON, Markdown, CSV, SQLite"],
        ["Semantic Search", "None", "Optional embeddings support"],
        ["Image Generation", "None", "Nano Banana Pro integration"],
        ["Command Analytics", "None", "Slash command/skill usage tracking"],
        ["Security Hardening", "None", "XSS/CSRF protection, CSP headers"],
    ]

    # Custom table with checkmarks
    table = Table(comparison_data, colWidths=[2.2*inch, 1.5*inch, 2.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        # Highlight OmniCortex column
        ('TEXTCOLOR', (2, 1), (2, -1), PRIMARY_BLUE),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    elements.append(PageBreak())

    # Key Differentiators
    elements.append(Paragraph("Key Differentiators", styles['SectionHeading']))

    elements.append(Paragraph("Knowledge Graph", styles['SubHeading']))
    elements.append(Paragraph(
        "OmniCortex allows you to link memories together with typed relationships (related_to, supersedes, "
        "derived_from, contradicts), creating a navigable knowledge graph visualized in the dashboard.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Project Management", styles['SubHeading']))
    elements.append(Paragraph(
        "Easily manage multiple projects with configurable scan directories, manual project registration, "
        "and favorites for quick access. All settings persist in ~/.omni-cortex/projects.json.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Freshness Management", styles['SubHeading']))
    elements.append(Paragraph(
        "Memories have status tracking (fresh, needs_review, outdated, archived) with configurable "
        "staleness thresholds. The Review tab helps you maintain knowledge quality over time.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Complete Audit Trail", styles['SubHeading']))
    elements.append(Paragraph(
        "Every tool call is logged with input, output, timing, and success status. The Activity tab "
        "provides full visibility into what Claude has done during your sessions.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Cross-Project Search", styles['SubHeading']))
    elements.append(Paragraph(
        "The global index at ~/.omni-cortex/global.db enables searching across all your projects. "
        "Find patterns and solutions from previous projects instantly.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Image Generation (Nano Banana Pro)", styles['SubHeading']))
    elements.append(Paragraph(
        "Generate visual content directly from your memories using Gemini 3 Pro. Create infographics, "
        "workflow diagrams, quote cards, and more with 8 preset templates and full customization.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Command & Skill Analytics", styles['SubHeading']))
    elements.append(Paragraph(
        "Track which slash commands and skills you use most, with scope differentiation (universal vs project). "
        "Monitor MCP server integration metrics and view success rates for all tool calls.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Security Hardening", styles['SubHeading']))
    elements.append(Paragraph(
        "Production-ready security with XSS protection (DOMPurify), path traversal prevention, "
        "security headers (CSP, X-Frame-Options), and prompt injection protection for LLM integrations.",
        styles['OmniBody']
    ))
    elements.append(Spacer(1, 20))

    # When to Use What
    elements.append(Paragraph("When to Use What", styles['SectionHeading']))
    when_data = [
        ["Scenario", "Recommendation"],
        ["Simple note-taking", "Basic MCP may suffice"],
        ["Project-specific knowledge", "OmniCortex (project DB)"],
        ["Cross-project patterns", "OmniCortex (global search)"],
        ["Team knowledge base", "OmniCortex (export & share)"],
        ["Long-running projects", "OmniCortex (freshness management)"],
        ["Complex codebases", "OmniCortex (relationships + graph)"],
    ]
    elements.append(create_table(when_data, [2.5*inch, 3.5*inch]))
    elements.append(Spacer(1, 30))

    # Footer
    elements.append(create_callout_box(
        "<b>OmniCortex</b> | github.com/AllCytes/Omni-Cortex",
        GREEN_ACCENT
    ))

    def on_page(canvas, doc):
        header_footer(canvas, doc, "Feature Comparison")

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    print("Generated: OmniCortex_FeatureComparison.pdf")


if __name__ == "__main__":
    print("Generating updated OmniCortex PDF documentation...")
    print("-" * 50)
    generate_dashboard_guide()
    generate_storage_architecture()
    generate_quickstart()
    generate_troubleshooting()
    generate_feature_comparison()
    print("-" * 50)
    print("All PDFs generated successfully!")
