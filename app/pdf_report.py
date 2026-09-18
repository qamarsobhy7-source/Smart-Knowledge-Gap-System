"""
PDF report generator for the Smart Knowledge Gap System.

Creates a professional PDF report summarizing a student's assessment:
    - Header with student info
    - Overall mastery summary
    - Per-concept mastery table
    - Knowledge gaps section
    - Learning path
    - Improvement (if re-assessment exists)
"""

from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
    TA_CENTER,
)
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# COLOR PALETTE
# ============================================================
PRIMARY = colors.HexColor("#6366F1")
SUCCESS = colors.HexColor("#10B981")
WARNING = colors.HexColor("#F59E0B")
DANGER = colors.HexColor("#EF4444")
INFO = colors.HexColor("#3B82F6")
DARK = colors.HexColor("#1F2937")
GRAY = colors.HexColor("#6B7280")
LIGHT_BG = colors.HexColor("#F3F4F6")


# ============================================================
# STYLES
# ============================================================
def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=26,
        textColor=PRIMARY,
        spaceAfter=8,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=15,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        borderPadding=4,
    ))

    styles.add(ParagraphStyle(
        name="BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        textColor=DARK,
        leading=14,
    ))

    return styles


# ============================================================
# STATUS COLORS
# ============================================================
def status_color(gap_level):
    level = str(gap_level or "").lower().strip()
    if level == "strong":
        return SUCCESS
    if level == "adequate":
        return INFO
    if level == "weak":
        return WARNING
    return DANGER


# ============================================================
# MAIN FUNCTION
# ============================================================
def generate_student_report(
    student,
    diagnosis,
    priority,
    learning_path,
    overall_mastery=None,
    reassessments=None,
):
    """
    Generate a PDF report and return it as bytes.

    Args:
        student: dict with student_id, full_name, email
        diagnosis: list of dicts (concept_id, concept_name, mastery, gap_level, gap_score)
        priority: list of dicts (concept_name, priority_level, priority_score)
        learning_path: list of dicts (concept_name, difficulty, mastery)
        overall_mastery: float or None
        reassessments: list of dicts (concept_name, before_mastery, after_mastery, improvement) or None

    Returns:
        bytes of the generated PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Smart Knowledge Gap Report",
        author="Smart Knowledge Gap System",
    )

    styles = get_styles()
    story = []

    # ---------- HEADER ----------
    story.append(Paragraph("Smart Knowledge Gap Report", styles["ReportTitle"]))
    story.append(Paragraph(
        "Concept-level diagnostic &amp; personalized learning path",
        styles["ReportSubtitle"],
    ))

    # Student info table
    now = datetime.now().strftime("%B %d, %Y")
    student_name = student.get("full_name", "Student") if student else "Student"
    student_email = student.get("email", "") if student else ""

    info_data = [
        ["Student:", student_name],
        ["Email:", student_email or "-"],
        ["Report Date:", now],
    ]

    info_table = Table(info_data, colWidths=[3.5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8 * mm))

    # ---------- OVERALL MASTERY ----------
    if overall_mastery is not None:
        story.append(Paragraph("Overall Mastery", styles["SectionHeading"]))

        mastery_text = f"{overall_mastery:.1f}%"
        if overall_mastery >= 80:
            mastery_desc = "Excellent — you are mastering the material."
            mastery_color = SUCCESS
        elif overall_mastery >= 60:
            mastery_desc = "Good — keep working on the weaker concepts."
            mastery_color = INFO
        elif overall_mastery >= 40:
            mastery_desc = "Developing — focus on closing your knowledge gaps."
            mastery_color = WARNING
        else:
            mastery_desc = "Needs improvement — follow the learning path carefully."
            mastery_color = DANGER

        summary_data = [
            ["Overall Mastery", mastery_text],
            ["Status", mastery_desc],
        ]

        summary_table = Table(summary_data, colWidths=[5 * cm, 10.5 * cm])
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
            ("TEXTCOLOR", (1, 0), (1, 0), mastery_color),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 6 * mm))

    # ---------- CONCEPT TABLE ----------
    if diagnosis:
        story.append(Paragraph("Concept-by-Concept Mastery", styles["SectionHeading"]))

        table_data = [["#", "Concept", "Mastery", "Status"]]

        for i, item in enumerate(diagnosis, 1):
            table_data.append([
                str(i),
                str(item.get("concept_name", "")),
                f"{float(item.get('mastery', 0)):.1f}%",
                str(item.get("gap_level", "")),
            ])

        concept_table = Table(
            table_data,
            colWidths=[1 * cm, 9 * cm, 3 * cm, 3 * cm],
            repeatRows=1,
        )

        style = [
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]

        # Color the status cells
        for i, item in enumerate(diagnosis, 1):
            color = status_color(item.get("gap_level"))
            style.append(("TEXTCOLOR", (3, i), (3, i), color))
            style.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))

        concept_table.setStyle(TableStyle(style))
        story.append(concept_table)
        story.append(Spacer(1, 6 * mm))

    # ---------- KNOWLEDGE GAPS ----------
    if diagnosis:
        gaps = [
            item for item in diagnosis
            if str(item.get("gap_level", "")).lower() in ("weak", "critical")
        ]

        if gaps:
            story.append(Paragraph("Knowledge Gaps", styles["SectionHeading"]))

            for item in gaps:
                color = status_color(item.get("gap_level"))
                text = (
                    f"<b>{item.get('concept_name', '')}</b> — "
                    f"<font color='{color.hexval()}'>{item.get('gap_level', '')}</font> "
                    f"(Mastery: {float(item.get('mastery', 0)):.1f}%, "
                    f"Gap Score: {float(item.get('gap_score', 0)):.1f})"
                )
                story.append(Paragraph(text, styles["BodyText2"]))
                story.append(Spacer(1, 2 * mm))
        else:
            story.append(Paragraph("Knowledge Gaps", styles["SectionHeading"]))
            story.append(Paragraph(
                "No significant gaps detected. Excellent work!",
                styles["BodyText2"],
            ))

        story.append(Spacer(1, 4 * mm))

    # ---------- LEARNING PATH ----------
    if learning_path:
        story.append(Paragraph("Personalized Learning Path", styles["SectionHeading"]))

        table_data = [["Step", "Concept", "Difficulty", "Current Mastery"]]

        for i, item in enumerate(learning_path, 1):
            table_data.append([
                str(i),
                str(item.get("concept_name", "")),
                str(item.get("difficulty", "")),
                f"{float(item.get('mastery', 0)):.1f}%",
            ])

        path_table = Table(
            table_data,
            colWidths=[1.5 * cm, 7 * cm, 3.5 * cm, 4 * cm],
            repeatRows=1,
        )
        path_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(path_table)
        story.append(Spacer(1, 6 * mm))

    # ---------- REASSESSMENT ----------
    if reassessments:
        story.append(PageBreak())
        story.append(Paragraph("Re-assessment: Before vs After", styles["SectionHeading"]))

        table_data = [["Concept", "Before", "After", "Improvement"]]

        for item in reassessments:
            imp = float(item.get("improvement", 0))
            imp_str = f"+{imp:.1f}%" if imp >= 0 else f"{imp:.1f}%"
            table_data.append([
                str(item.get("concept_name", "")),
                f"{float(item.get('before_mastery', 0)):.1f}%",
                f"{float(item.get('after_mastery', 0)):.1f}%",
                imp_str,
            ])

        ra_table = Table(
            table_data,
            colWidths=[8 * cm, 3 * cm, 3 * cm, 3 * cm],
            repeatRows=1,
        )

        style = [
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]

        for i, item in enumerate(reassessments, 1):
            imp = float(item.get("improvement", 0))
            color = SUCCESS if imp >= 0 else DANGER
            style.append(("TEXTCOLOR", (3, i), (3, i), color))
            style.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))

        ra_table.setStyle(TableStyle(style))
        story.append(ra_table)

    # ---------- FOOTER ----------
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph(
        "<i>Generated by Smart Knowledge Gap &amp; Personalized Learning System</i>",
        styles["ReportSubtitle"],
    ))

    # Build
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
