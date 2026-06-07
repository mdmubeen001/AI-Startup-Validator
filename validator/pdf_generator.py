"""
pdf_generator.py — AI Startup Validator
Professional investor-ready PDF report generator using ReportLab + Matplotlib.

Required packages (add to requirements.txt):
    reportlab>=4.0
    matplotlib>=3.7
"""

import io
import math
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable, Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─────────────────────────────────────────────
# BRAND PALETTE
# ─────────────────────────────────────────────
DARK_NAVY   = colors.HexColor("#0D1B2A")   # deep navy – headings / cover bg
ACCENT_BLUE = colors.HexColor("#1A73E8")   # primary accent
LIGHT_BLUE  = colors.HexColor("#E8F0FE")   # section tint backgrounds
MID_GREY    = colors.HexColor("#5F6368")   # body text
LIGHT_GREY  = colors.HexColor("#F8F9FA")   # alternate row / panel
RULE_GREY   = colors.HexColor("#DADCE0")   # horizontal rules

GREEN_OK    = colors.HexColor("#1E7E34")
ORANGE_MED  = colors.HexColor("#D97706")
RED_HIGH    = colors.HexColor("#C0392B")

PAGE_W, PAGE_H = A4


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _verdict(score: float):
    """Return (colour, label) for a viability score."""
    if score >= 8:
        return GREEN_OK,   "Strong Startup Potential"
    if score >= 6:
        return ORANGE_MED, "Moderate Opportunity"
    return RED_HIGH,       "High Risk Startup"


def _safe_str(val, fallback="N/A"):
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback


def _parse_json(val, fallback=None):
    """Safely parse JSON from string, return fallback if fails."""
    if val is None:
        return fallback
    if isinstance(val, (dict, list)):
        return val
    try:
        import json
        return json.loads(str(val))
    except Exception:
        return fallback


def _parse_tam_sam_som(val, fallback=None):
    """Parse tam_sam_som, handling both JSON and old 'TAM:x,SAM:y,SOM:z' format."""
    if val is None:
        return fallback or {"tam": "N/A", "sam": "N/A", "som": "N/A"}
    if isinstance(val, dict):
        return val
    try:
        import json
        parsed = json.loads(str(val))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    # Try old comma-separated format: "TAM:$10B,SAM:$1B,SOM:$100M"
    result = {"tam": "N/A", "sam": "N/A", "som": "N/A"}
    try:
        parts = str(val).split(",")
        for part in parts:
            part = part.strip()
            if ":" in part:
                k, v = part.split(":", 1)
                k = k.strip().lower()
                v = v.strip()
                if k in ["tam", "sam", "som"]:
                    result[k] = v
    except Exception:
        pass
    return result


def _parse_competitors(val, fallback=None):
    """Parse competitors, handling JSON list or plain text."""
    if val is None:
        return fallback or []
    if isinstance(val, list):
        return val
    parsed = _parse_json(val)
    if isinstance(parsed, list):
        return parsed
    # If plain text, split into lines or single item
    val_str = str(val).strip()
    if val_str:
        return [{"name": "Competitor", "description": val_str}]
    return []


def _parse_list_or_text(val, fallback=None):
    """Parse a value that could be JSON list or plain text."""
    if val is None:
        return fallback or []
    if isinstance(val, list):
        return val
    parsed = _parse_json(val)
    if isinstance(parsed, list):
        return parsed
    # If plain text, return as single-item list
    val_str = str(val).strip()
    if val_str:
        return [val_str]
    return fallback or []


def _bullet_paragraphs(items, style):
    """Convert a list of strings to bullet Paragraphs."""
    paras = []
    for item in items:
        text = _safe_str(item)
        paras.append(Paragraph(f"&bull;&nbsp;&nbsp;{text}", style))
        paras.append(Spacer(1, 3))
    return paras


# ─────────────────────────────────────────────
# CUSTOM FLOWABLES
# ─────────────────────────────────────────────

class ScoreBadge(Flowable):
    """Draws a circular score badge centred on the page."""

    def __init__(self, score, width=160, height=160):
        super().__init__()
        self.score = float(score)
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 - 6

        verdict_color, _ = _verdict(self.score)

        # Outer ring
        c.setStrokeColor(verdict_color)
        c.setLineWidth(6)
        c.setFillColor(colors.white)
        c.circle(cx, cy, radius, stroke=1, fill=1)

        # Inner subtle ring
        c.setStrokeColor(LIGHT_BLUE)
        c.setLineWidth(2)
        c.circle(cx, cy, radius - 10, stroke=1, fill=0)

        # Score number
        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 46)
        score_text = str(int(self.score)) if self.score == int(self.score) else f"{self.score:.1f}"
        c.drawCentredString(cx, cy + 6, score_text)

        # "/10" label
        c.setFillColor(MID_GREY)
        c.setFont("Helvetica", 16)
        c.drawCentredString(cx, cy - 18, "/ 10")


class VerticalSpacer(Flowable):
    def __init__(self, h):
        super().__init__()
        self.height = h
        self.width = 0

    def draw(self):
        pass


# ─────────────────────────────────────────────
# CHART GENERATOR
# ─────────────────────────────────────────────

def _build_radar_chart(analysis_data: dict) -> io.BytesIO:
    """Return a BytesIO PNG of a radar/spider chart derived from the analysis."""
    score = float(analysis_data.get("viability_score", 5))

    # Derive approximate sub-scores from available data
    competitors = analysis_data.get("competitors", [])
    comp_count  = len(competitors) if isinstance(competitors, list) else 3
    competition_risk  = max(1, min(10, 10 - comp_count))          # fewer = less risk
    market_potential  = min(10, score + 1.0)
    funding_readiness = min(10, score * 0.9)
    innovation_index  = min(10, score + 0.5)
    team_execution    = min(10, score * 0.95)

    categories = [
        "Viability\nScore",
        "Market\nPotential",
        "Funding\nReadiness",
        "Competition\nRisk",
        "Innovation\nIndex",
    ]
    values = [
        score,
        market_potential,
        funding_readiness,
        competition_risk,
        innovation_index,
    ]

    N = len(categories)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]
    values_plot = values + values[:1]

    fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("white")

    # Grid styling
    ax.set_facecolor("#F8F9FA")
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=9, color="#333333", fontweight="bold")
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], size=7, color="#999999")
    ax.yaxis.set_tick_params(labelsize=7)
    ax.grid(color="#DADCE0", linestyle="--", linewidth=0.8)

    # Fill
    fill_color = "#1A73E8"
    ax.plot(angles, values_plot, "o-", linewidth=2, color=fill_color)
    ax.fill(angles, values_plot, alpha=0.25, color=fill_color)

    ax.set_title("Startup Performance Radar", size=12, fontweight="bold",
                 color="#0D1B2A", pad=20)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _build_bar_chart(analysis_data: dict) -> io.BytesIO:
    """Return a BytesIO PNG of a horizontal bar chart."""
    score = float(analysis_data.get("viability_score", 5))
    competitors = analysis_data.get("competitors", [])
    comp_count  = len(competitors) if isinstance(competitors, list) else 3

    categories = ["Viability Score", "Market Potential",
                  "Funding Readiness", "Competition Risk", "Innovation Index"]
    raw_values = [
        score,
        min(10, score + 1.0),
        min(10, score * 0.9),
        max(1, min(10, 10 - comp_count)),
        min(10, score + 0.5),
    ]

    bar_colors = []
    for v in raw_values:
        if v >= 7:
            bar_colors.append("#1E7E34")
        elif v >= 5:
            bar_colors.append("#D97706")
        else:
            bar_colors.append("#C0392B")

    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#F8F9FA")

    y_pos = np.arange(len(categories))
    bars = ax.barh(y_pos, raw_values, color=bar_colors, height=0.5,
                   edgecolor="white", linewidth=0.8)

    # Value labels
    for bar, val in zip(bars, raw_values):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", ha="left", fontsize=9,
                fontweight="bold", color="#0D1B2A")

    ax.set_xlim(0, 11.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=9, color="#333333")
    ax.set_xlabel("Score (out of 10)", fontsize=9, color="#5F6368")
    ax.set_title("Key Performance Indicators", fontsize=11, fontweight="bold",
                 color="#0D1B2A", pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#DADCE0")
    ax.spines["bottom"].set_color("#DADCE0")
    ax.grid(axis="x", color="#DADCE0", linestyle="--", linewidth=0.6)
    ax.set_axisbelow(True)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────
# STYLE SHEET
# ─────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()

    styles = {
        # Cover page
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=36,
            textColor=DARK_NAVY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            fontName="Helvetica",
            fontSize=14,
            leading=20,
            textColor=MID_GREY,
            alignment=TA_CENTER,
            spaceAfter=40,
        ),
        "cover_label": ParagraphStyle(
            "cover_label",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#90A4AE"),
            alignment=TA_CENTER,
        ),
        "cover_value": ParagraphStyle(
            "cover_value",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=22,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        # Section headings
        "section_heading": ParagraphStyle(
            "section_heading",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=20,
            textColor=DARK_NAVY,
            spaceBefore=18,
            spaceAfter=6,
        ),
        "sub_heading": ParagraphStyle(
            "sub_heading",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            textColor=ACCENT_BLUE,
            spaceBefore=10,
            spaceAfter=4,
        ),
        # Body
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=MID_GREY,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=MID_GREY,
            leftIndent=10,
            spaceAfter=2,
        ),
        # Executive summary
        "exec_body": ParagraphStyle(
            "exec_body",
            fontName="Helvetica",
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=8,
            alignment=TA_JUSTIFY,
        ),
        # Score / verdict
        "verdict": ParagraphStyle(
            "verdict",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        # Branding card label
        "card_label": ParagraphStyle(
            "card_label",
            fontName="Helvetica",
            fontSize=9,
            textColor=MID_GREY,
            alignment=TA_CENTER,
        ),
        "card_value": ParagraphStyle(
            "card_value",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=DARK_NAVY,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        # Footer / meta
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#9E9E9E"),
            alignment=TA_CENTER,
        ),
    }
    return styles


# ─────────────────────────────────────────────
# PAGE TEMPLATES (header / footer callbacks)
# ─────────────────────────────────────────────

class _ReportDocTemplate(BaseDocTemplate):
    """Custom doc template that injects footer on every non-cover page."""

    def __init__(self, filename, startup_name, **kwargs):
        self.startup_name = startup_name
        super().__init__(filename, **kwargs)

    def handle_pageBegin(self):
        super().handle_pageBegin()

    def afterPage(self):
        pass  # handled by onPage callbacks


def _cover_on_page(canvas, doc):
    """Cover page — no footer, full navy background."""
    canvas.saveState()
    # Full-page navy background
    #canvas.setFillColor(DARK_NAVY)
    #canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Accent stripe at top
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H - 6, PAGE_W, 6, stroke=0, fill=1)

    # Subtle bottom accent stripe
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, 0, PAGE_W, 4, stroke=0, fill=1)

    canvas.restoreState()


def _content_on_page(canvas, doc):
    """Content pages — light header stripe + footer."""
    canvas.saveState()

    # Top thin accent line
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H - 3, PAGE_W, 3, stroke=0, fill=1)

    # Footer bar
    footer_y = 22
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, 0, PAGE_W, footer_y, stroke=0, fill=1)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(cm * 1.5, footer_y / 2 - 3,
                      f"AI Startup Validator  |  {getattr(doc, 'startup_name', '')}")
    canvas.drawCentredString(PAGE_W / 2, footer_y / 2 - 3, "Generated Report")
    canvas.drawRightString(PAGE_W - cm * 1.5, footer_y / 2 - 3,
                           f"Page {doc.page}")

    canvas.restoreState()


# ─────────────────────────────────────────────
# SECTION BUILDERS
# ─────────────────────────────────────────────

def _section_rule(styles):
    return [
        HRFlowable(
            width="100%", thickness=1,
            color=RULE_GREY, spaceAfter=6, spaceBefore=2,
        )
    ]


def _section_header(title: str, styles) -> list:
    return [
        Paragraph(title, styles["section_heading"]),
        HRFlowable(width="100%", thickness=1.5,
                   color=ACCENT_BLUE, spaceAfter=8, spaceBefore=0),
    ]


def _build_cover(analysis_data: dict, styles: dict) -> list:
    story = []
    startup_name = _safe_str(analysis_data.get("startup_name") or
                             analysis_data.get("startup_name_suggestions", ["Your Startup"])[0]
                             if isinstance(analysis_data.get("startup_name_suggestions"), list)
                             else analysis_data.get("startup_name_suggestions"),
                             "Your Startup")
    industry     = _safe_str(analysis_data.get("industry"))
    today        = datetime.now().strftime("%B %d, %Y")

    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph("AI Startup Validator", styles["cover_title"]))
    story.append(Paragraph("Professional Startup Validation Report", styles["cover_subtitle"]))
    story.append(Spacer(1, 1.2 * cm))

    # Divider line
    story.append(HRFlowable(width="60%", thickness=1,
                             color=colors.HexColor("#1A73E8"),
                             hAlign="CENTER", spaceAfter=1.5 * cm))

    # Meta table
    meta = [
        ["STARTUP NAME", startup_name],
        ["INDUSTRY",     industry],
        ["REPORT DATE",  today],
    ]
    meta_table = Table(meta, colWidths=[6 * cm, 10 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica"),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.HexColor("#90A4AE")),
        ("TEXTCOLOR",   (1, 0), (1, -1), DARK_NAVY),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN",       (0, 0), (-1, -1), "LEFT"),
        ("LINEBELOW",   (0, 0), (-1, -2), 0.5, colors.HexColor("#263850")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 2.5 * cm))

    # Confidential tag
    conf_table = Table([["CONFIDENTIAL — FOR INVESTOR REVIEW ONLY"]],
                       colWidths=[14 * cm])
    conf_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#1A73E8")),
        ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(conf_table)

    story.append(PageBreak())
    return story


def _build_exec_summary(analysis_data: dict, styles: dict) -> list:
    story = []
    story.append(Spacer(1, 0.6 * cm))
    story += _section_header("Executive Summary", styles)

    description = _safe_str(analysis_data.get("startup_description") or
                            analysis_data.get("description"))
    market      = _safe_str(analysis_data.get("market_analysis") or
                            analysis_data.get("market_opportunity"))
    score       = float(analysis_data.get("viability_score", 5))
    verdict_col, verdict_label = _verdict(score)
    pitch       = _safe_str(analysis_data.get("investor_pitch"))

    exec_blocks = [
        ("<b>Startup Concept</b>", description),
        ("<b>Market Opportunity</b>", market),
        ("<b>Investor Pitch</b>", pitch),
    ]

    for label, content in exec_blocks:
        if content and content != "N/A":
            story.append(Paragraph(label, styles["sub_heading"]))
            story.append(Paragraph(content, styles["exec_body"]))

    # Recommendation pill
    rec_text = (
        f"Overall Recommendation: Based on the analysis, this startup demonstrates "
        f"<b>{verdict_label}</b> with a viability score of <b>{score}/10</b>. "
        f"The evaluation reflects market conditions, competitive landscape, and business model strength."
    )
    rec_para = Paragraph(rec_text, styles["exec_body"])
    rec_table = Table([[rec_para]], colWidths=[16.5 * cm])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("BOX",           (0, 0), (-1, -1), 1, ACCENT_BLUE),
    ]))
    story.append(Spacer(1, 8))
    story.append(rec_table)
    story.append(Spacer(1, 14))
    return story


def _build_score_section(analysis_data: dict, styles: dict) -> list:
    story = []
    story += _section_header("Viability Score", styles)

    score = float(analysis_data.get("viability_score", 5))
    verdict_col, verdict_label = _verdict(score)

    badge = ScoreBadge(score, width=160, height=160)
    badge.hAlign = "CENTER"
    story.append(badge)
    story.append(Spacer(1, 8))

    verdict_para = Paragraph(
        f'<font color="{verdict_col.hexval()}"><b>{verdict_label}</b></font>',
        styles["verdict"],
    )
    story.append(verdict_para)
    story.append(Spacer(1, 14))
    return story


def _build_swot(analysis_data: dict, styles: dict) -> list:
    story = []
    story += _section_header("SWOT Analysis", styles)

    swot = analysis_data.get("swot_analysis", {})
    # Ensure swot is dict
    swot = _parse_json(swot, {}) if not isinstance(swot, dict) else swot
    if not isinstance(swot, dict):
        story.append(Paragraph(_safe_str(swot), styles["body"]))
        return story

    icons = {
        "strengths":    ("&#x2705;", "Strengths",    colors.HexColor("#E8F5E9"), colors.HexColor("#1E7E34")),
        "weaknesses":   ("&#x26A0;", "Weaknesses",   colors.HexColor("#FFF8E1"), colors.HexColor("#D97706")),
        "opportunities":("&#x1F680;", "Opportunities", colors.HexColor("#E3F2FD"), colors.HexColor("#1A73E8")),
        "threats":      ("&#x1F6E1;", "Threats",      colors.HexColor("#FFEBEE"), colors.HexColor("#C0392B")),
    }

    cells = []
    for key, (icon, label, bg, accent) in icons.items():
        items = swot.get(key, swot.get(key.capitalize(), []))
        items = _parse_list_or_text(items, [])

        header_para = Paragraph(
            f'<font color="{accent.hexval()}"><b>{icon} {label}</b></font>',
            ParagraphStyle("swot_hdr", fontName="Helvetica-Bold",
                           fontSize=11, leading=16, textColor=accent)
        )
        content_paras = [header_para, Spacer(1, 4)]
        if items:
            content_paras += _bullet_paragraphs(items, styles["bullet"])
        else:
            content_paras.append(Paragraph("No data available.", styles["bullet"]))

        cell_table = Table([[content_paras]], colWidths=[7.8 * cm])
        cell_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("BOX",           (0, 0), (-1, -1), 1, RULE_GREY),
        ]))
        cells.append(cell_table)

    # 2×2 grid
    swot_grid = Table(
        [[cells[0], cells[1]], [cells[2], cells[3]]],
        colWidths=[8.25 * cm, 8.25 * cm],
        rowHeights=None,
    )
    swot_grid.setStyle(TableStyle([
        ("VALIGN",   (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("INNERGRID",    (0, 0), (-1, -1), 4, colors.white),
    ]))
    story.append(swot_grid)
    story.append(Spacer(1, 14))
    return story


def _build_market_analysis(analysis_data: dict, styles: dict) -> list:
    story = []
    story += _section_header("Market Analysis", styles)

    market = analysis_data.get("market_analysis", "")
    # Try to parse as JSON if string
    if not isinstance(market, (dict, str)):
        market = _safe_str(market)
    if isinstance(market, dict):
        for k, v in market.items():
            story.append(Paragraph(k.replace("_", " ").title(), styles["sub_heading"]))
            story.append(Paragraph(_safe_str(v), styles["body"]))
    else:
        story.append(Paragraph(_safe_str(market), styles["body"]))

    # TAM / SAM / SOM
    tam_data = _parse_tam_sam_som(analysis_data.get("tam_sam_som", {}))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Market Sizing", styles["sub_heading"]))
    rows = []
    for label in ["TAM", "SAM", "SOM"]:
        key = label.lower()
        val = tam_data.get(key) or tam_data.get(label, "N/A")
        rows.append([label, _safe_str(val)])

    tam_table = Table(rows, colWidths=[3 * cm, 13.5 * cm])
    tam_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), DARK_NAVY),
        ("BACKGROUND",    (1, 0), (1, -1), colors.white),
        ("ROWBACKGROUNDS",(1, 0), (1, -1), [LIGHT_GREY, colors.white]),
        ("TEXTCOLOR",     (0, 0), (0, -1), colors.white),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, RULE_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, RULE_GREY),
    ]))
    story.append(tam_table)

    story.append(Spacer(1, 14))
    return story


def _build_competitors(analysis_data: dict, styles: dict) -> list:
    story = []
    story += _section_header("Competitive Landscape", styles)

    competitors = _parse_competitors(analysis_data.get("competitors", []))
    if not competitors:
        story.append(Paragraph("No competitor data available.", styles["body"]))
        story.append(Spacer(1, 14))
        return story

    rows = [["#", "Competitor", "Notes"]]
    for i, comp in enumerate(competitors, 1):
        if isinstance(comp, dict):
            name  = _safe_str(comp.get("name") or comp.get("competitor"))
            notes = _safe_str(comp.get("description") or comp.get("notes") or "—")
        else:
            name  = _safe_str(comp)
            notes = "—"
        rows.append([
        str(i),
        Paragraph(name, styles["body"]),
        Paragraph(notes, styles["body"])
        ])

    col_w = [1 * cm, 3.5 * cm, 12 * cm]
    comp_table = Table(rows, colWidths=col_w, repeatRows=1)
    comp_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK_NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9.5),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 1, RULE_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, RULE_GREY),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(comp_table)

    story.append(Spacer(1, 14))
    return story


def _build_business_strategy(analysis_data: dict, styles: dict) -> list:
    story = []
    story += _section_header("Business Strategy", styles)

    model   = _safe_str(analysis_data.get("business_model"))
    funding = _safe_str(analysis_data.get("funding_requirement") or
                        analysis_data.get("funding_requirements"))
    risks   = _parse_list_or_text(analysis_data.get("risk_analysis", []))
    improvements = _parse_list_or_text(
        analysis_data.get("improvement_suggestions") or \
        analysis_data.get("improvements", [])
    )

    if model and model != "N/A":
        story.append(Paragraph("Business Model", styles["sub_heading"]))
        story.append(Paragraph(model, styles["body"]))

    if funding and funding != "N/A":
        story.append(Paragraph("Funding Requirement", styles["sub_heading"]))
        story.append(Paragraph(funding, styles["body"]))

    if risks:
        story.append(Paragraph("Risk Analysis", styles["sub_heading"]))
        story += _bullet_paragraphs(risks, styles["bullet"])

    if improvements:
        story.append(Paragraph("Improvement Suggestions", styles["sub_heading"]))
        story += _bullet_paragraphs(improvements, styles["bullet"])

    story.append(Spacer(1, 14))
    return story


def _build_charts(analysis_data: dict) -> list:
    story = []

    radar_buf = _build_radar_chart(analysis_data)
    bar_buf   = _build_bar_chart(analysis_data)

    radar_img = Image(radar_buf, width=9 * cm, height=9 * cm)
    bar_img   = Image(bar_buf,   width=10 * cm, height=5.5 * cm)

    # Side-by-side
    chart_table = Table(
        [[radar_img, bar_img]],
        colWidths=[9.5 * cm, 10 * cm],
    )
    chart_table.setStyle(TableStyle([
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(chart_table)
    story.append(Spacer(1, 14))
    return story


def _build_branding(analysis_data: dict, styles: dict) -> list:
    story = []
    story += _section_header("Branding & Identity", styles)

    suggestions = analysis_data.get("startup_name_suggestions", [])
    tagline     = _safe_str(analysis_data.get("tagline"))

    if suggestions:
        # Handle suggestions: could be JSON list or comma-separated string
        if isinstance(suggestions, str):
            # Try parsing as JSON first
            parsed = _parse_json(suggestions)
            if isinstance(parsed, list):
                suggestions = parsed
            else:
                # Try comma-separated
                suggestions = [s.strip() for s in suggestions.split(",") if s.strip()]
        
        # Ensure it's a list
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)]
        
        # Filter out empty
        suggestions = [s for s in suggestions if str(s).strip()]
        
        if suggestions:
            story.append(Paragraph("Startup Name Suggestions", styles["sub_heading"]))
            cards = []
            for name in suggestions[:6]:
                card_para = [
                    Paragraph(_safe_str(name), styles["card_value"]),
                    Paragraph("Suggested Name", styles["card_label"]),
                ]
                card = Table([[card_para]], colWidths=[4.8 * cm])
                card.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BLUE),
                    ("BOX",           (0, 0), (-1, -1), 1, ACCENT_BLUE),
                    ("TOPPADDING",    (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ]))
                cards.append(card)

            # Fill to 3-per-row
            per_row = 3
            while len(cards) % per_row != 0:
                cards.append(Spacer(4.8 * cm, 1))

            rows_data = [cards[i:i + per_row] for i in range(0, len(cards), per_row)]
            names_table = Table(rows_data,
                                colWidths=[5.5 * cm] * per_row)
            names_table.setStyle(TableStyle([
                ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(names_table)
            story.append(Spacer(1, 10))

    if tagline and tagline != "N/A":
        story.append(Paragraph("Brand Tagline", styles["sub_heading"]))
        tl_para = Paragraph(f'<i>"{tagline}"</i>',
                            ParagraphStyle("tl", fontName="Helvetica-Oblique",
                                           fontSize=13, leading=18,
                                           textColor=DARK_NAVY,
                                           alignment=TA_CENTER))
        tl_table = Table([[tl_para]], colWidths=[16.5 * cm])
        tl_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BLUE),
            ("BOX",           (0, 0), (-1, -1), 1.5, ACCENT_BLUE),
            ("TOPPADDING",    (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ]))
        story.append(tl_table)

    story.append(Spacer(1, 14))
    return story


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def generate_pdf_report(analysis_data: dict, output_path: str) -> str:
    """
    Generate a professional investor-ready PDF report.

    Parameters
    ----------
    analysis_data : dict
        The structured JSON returned by the AI analysis step.
        Expected keys (all optional — graceful fallbacks used):
            startup_name, industry, startup_description, viability_score,
            swot_analysis, market_analysis, tam_sam_som, competitors,
            business_model, funding_requirement, risk_analysis,
            improvement_suggestions, investor_pitch,
            startup_name_suggestions, tagline
    output_path : str
        Absolute or relative file path for the output PDF.

    Returns
    -------
    str
        The output_path string (for convenience).
    """

    startup_name = _safe_str(
        analysis_data.get("startup_name") or
        (analysis_data.get("startup_name_suggestions", ["Startup"])[0]
         if isinstance(analysis_data.get("startup_name_suggestions"), list)
         else analysis_data.get("startup_name_suggestions")),
        "Startup"
    )

    styles = _build_styles()

    # ── Document setup ──────────────────────────────────────────────────
    doc = _ReportDocTemplate(
        output_path,
        startup_name=startup_name,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
    )

    CONTENT_W = PAGE_W - 3 * cm  # 16.7 cm usable

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H,
                        leftPadding=2 * cm, rightPadding=2 * cm,
                        topPadding=0, bottomPadding=0,
                        id="cover")

    content_frame = Frame(
        doc.leftMargin, doc.bottomMargin + 22,   # 22pt for footer
        CONTENT_W, PAGE_H - doc.topMargin - doc.bottomMargin - 22,
        id="content"
    )

    cover_template   = PageTemplate(id="Cover",   frames=[cover_frame],
                                    onPage=_cover_on_page)
    content_template = PageTemplate(id="Content", frames=[content_frame],
                                    onPage=_content_on_page)
    doc.addPageTemplates([cover_template, content_template])

    # ── Story assembly ───────────────────────────────────────────────────
    story = []

    # 1. Cover
    story.append(NextPageTemplate("Cover"))
    story += _build_cover(analysis_data, styles)

    # Switch to content template for all remaining pages
    story.append(NextPageTemplate("Content"))

    # 2. Executive Summary
    story += _build_exec_summary(analysis_data, styles)

    # 3. Viability Score Badge
    story += _build_score_section(analysis_data, styles)

    # 4. Charts — kept together so heading never orphans on its own page
    charts_block = _section_header("Performance Charts", styles) + _build_charts(analysis_data)
    story.append(KeepTogether(charts_block))

    # 5. SWOT Analysis
    story += _build_swot(analysis_data, styles)

    # 6. Market Analysis
    story += _build_market_analysis(analysis_data, styles)

    # 7. Competitive Landscape
    story += _build_competitors(analysis_data, styles)

    # 8. Business Strategy
    story += _build_business_strategy(analysis_data, styles)

    # 9. Branding
    story += _build_branding(analysis_data, styles)

    # ── Build ────────────────────────────────────────────────────────────
    doc.build(story)
    return output_path
def generate_pdf(data, filename):
    return generate_pdf_report(data, filename)