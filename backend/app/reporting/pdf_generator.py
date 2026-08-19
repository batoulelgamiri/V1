from __future__ import annotations

from html import escape
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.database.models import Analysis
from app.schemas.report import StructuredReport


class PDFGenerationError(RuntimeError):
    pass


def generate_pdf(analysis: Analysis, report: StructuredReport, output_path: Path) -> Path:
    if analysis.classification not in {"suspicious", "malicious"}:
        raise ValueError("PDF reports are generated only for suspicious or malicious analyses.")
    if report.classification_result != analysis.classification:
        raise ValueError("Report classification does not match the stored analysis.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleAegis",
            parent=styles["Title"],
            textColor=colors.HexColor("#0B2D36"),
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionAegis",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#0D6974"),
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            spaceBefore=12,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["BodyText"],
            textColor=colors.HexColor("#52666D"),
            fontSize=8,
            leading=11,
        )
    )

    def paragraph(value: object, style: str = "BodyText") -> Paragraph:
        return Paragraph(escape(str(value)).replace("\n", "<br/>"), styles[style])

    story = [
        Paragraph("AEGIS PE INTELLIGENCE", styles["TitleAegis"]),
        paragraph("Static malware analysis report", "SmallMuted"),
        Spacer(1, 7 * mm),
    ]
    metadata = [
        ["File", analysis.original_filename],
        ["SHA-256", analysis.sha256],
        ["Analyzed", (analysis.created_at or datetime.now(timezone.utc)).isoformat()],
        ["Source", analysis.source],
        ["Classification", analysis.classification.upper()],
        ["XGBoost malicious probability", f"{(analysis.score or 0) * 100:.2f}%"],
        ["Model", f"{analysis.model_name} / {analysis.model_version}"],
    ]
    table = Table([[paragraph(k, "SmallMuted"), paragraph(v)] for k, v in metadata], colWidths=[38 * mm, 130 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF3F4")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7CDD1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D4E1E3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([table, paragraph("Executive summary", "SectionAegis"), paragraph(report.executive_summary)])

    def add_bullets(title: str, items: list[str]) -> None:
        story.append(paragraph(title, "SectionAegis"))
        if not items:
            story.append(paragraph("No supported items identified.", "SmallMuted"))
        for item in items:
            story.append(paragraph(f"- {item}"))
            story.append(Spacer(1, 2 * mm))

    add_bullets(
        "Confirmed indicators",
        [f"{item.indicator}: {item.evidence}" for item in report.confirmed_indicators],
    )
    add_bullets(
        "Suspected capabilities",
        [
            f"{item.capability} ({item.confidence} confidence) - {'; '.join(item.evidence)}"
            for item in report.suspected_capabilities
        ],
    )
    add_bullets(
        "MITRE ATT&CK mappings",
        [
            f"{item.technique_id} {item.technique_name} ({item.confidence}) - {item.evidence}"
            for item in report.mitre_attack
        ],
    )
    add_bullets("Analyst recommendations", report.recommendations)
    add_bullets("Limitations", report.limitations)

    try:
        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=f"Aegis analysis {analysis.id}",
            author="Aegis PE Intelligence",
        )
        document.build(story)
    except Exception as exc:
        output_path.unlink(missing_ok=True)
        raise PDFGenerationError(f"Unable to generate PDF: {exc}") from exc
    return output_path
