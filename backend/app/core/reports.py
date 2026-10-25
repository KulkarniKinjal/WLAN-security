"""
Report generation: one PDF (via reportlab, which is pure-Python and
installs reliably on Windows/Kali without native build tools) and one
JSON export per session. Both always disclose execution_mode and
fixture_provenance so a demonstration-mode result can never be mistaken
for a verified real experiment.
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.models.session import Session as SessionModel


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="SectionHead", fontSize=12, spaceAfter=6, spaceBefore=12, textColor=colors.HexColor("#22354B")))
    return ss


def generate_json_report(session: SessionModel) -> Path:
    data = {
        "session_id": session.id,
        "name": session.name,
        "module": session.module.value,
        "scenario_id": session.scenario_id,
        "status": session.status.value,
        "outcome": session.outcome.value,
        "execution_mode": session.execution_mode.value,
        "fixture_provenance": session.fixture_provenance,
        "input_summary": session.input_summary,
        "evidence": session.evidence,
        "explanation": session.explanation,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "finished_at": session.finished_at.isoformat() if session.finished_at else None,
        "duration_seconds": session.duration_seconds,
    }
    out_path = Path(settings.reports_dir) / f"{session.id}.json"
    out_path.write_text(json.dumps(data, indent=2))
    return out_path


def generate_pdf_report(session: SessionModel) -> Path:
    styles = _styles()
    out_path = Path(settings.reports_dir) / f"{session.id}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    story = []

    story.append(Paragraph("WLAN AttackLab -- Session Report", styles["Title"]))
    story.append(Paragraph(f"Session: {session.name}", styles["Normal"]))
    story.append(Paragraph(f"Created: {session.created_at}", styles["Normal"]))
    mode_label = "REAL LAB EXECUTION" if session.execution_mode.value == "real" else "DEMONSTRATION MODE (not a real execution)"
    story.append(Paragraph(f"<b>Execution mode: {mode_label}</b>", styles["Normal"]))
    story.append(Spacer(1, 8))

    meta_table = Table([
        ["Module", session.module.value],
        ["Scenario", session.scenario_id],
        ["Status", session.status.value],
        ["Security outcome", session.outcome.value],
        ["Fixture provenance", session.fixture_provenance or "n/a"],
    ], colWidths=[140, 320])
    meta_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B9C6D1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2F8")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(meta_table)

    exp = session.explanation or {}
    for key, title in (
        ("objective", "Objective"),
        ("proves", "What the result proves"),
        ("does_not_prove", "What the result does NOT prove"),
        ("defense", "Recommended defense"),
    ):
        if exp.get(key):
            story.append(Paragraph(title, styles["SectionHead"]))
            story.append(Paragraph(str(exp[key]), styles["Normal"]))

    story.append(Paragraph("Evidence (excerpt)", styles["SectionHead"]))
    ev_text = json.dumps(session.evidence, indent=2)[:3000]
    story.append(Paragraph(f"<font face='Courier' size=8>{_escape(ev_text)}</font>", styles["Normal"]))

    story.append(Paragraph("Limitations", styles["SectionHead"]))
    story.append(Paragraph(
        "This report reflects a single bounded lab experiment against an authorized, isolated "
        "target or offline capture. It does not constitute a general security assessment of any "
        "production network, and a 'not found' wordlist result does not imply a password is strong.",
        styles["Normal"],
    ))

    doc.build(story)
    return out_path


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>"))
