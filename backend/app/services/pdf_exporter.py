from __future__ import annotations

import io
from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.ai_system import AISystem, RiskCategory
from app.models.audit_log import AuditLog
from app.models.model_card import ModelCard
from app.models.risk_assessment import RiskAssessment

RISK_COLORS = {
    RiskCategory.PROHIBITED: colors.HexColor("#DC2626"),
    RiskCategory.HIGH_RISK: colors.HexColor("#EA580C"),
    RiskCategory.LIMITED_RISK: colors.HexColor("#CA8A04"),
    RiskCategory.MINIMAL_RISK: colors.HexColor("#16A34A"),
}

RISK_LABELS = {
    RiskCategory.PROHIBITED: "INTERDIT (Art. 5 AI Act)",
    RiskCategory.HIGH_RISK: "Haut risque (Annexe III AI Act)",
    RiskCategory.LIMITED_RISK: "Risque limité",
    RiskCategory.MINIMAL_RISK: "Risque minimal",
}


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontSize=20, spaceAfter=6, textColor=colors.HexColor("#1E3A5F")),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=14, spaceBefore=14, spaceAfter=4, textColor=colors.HexColor("#1E3A5F")),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=11, spaceBefore=10, spaceAfter=3, textColor=colors.HexColor("#374151")),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=9, spaceAfter=4, leading=14),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#6B7280")),
        "label": ParagraphStyle("label", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#6B7280"), spaceAfter=1),
        "value": ParagraphStyle("value", parent=base["Normal"], fontSize=9, spaceAfter=6, leading=13),
        "risk_badge": ParagraphStyle("risk_badge", parent=base["Normal"], fontSize=13, fontName="Helvetica-Bold"),
    }


def generate_compliance_report(
    system: AISystem,
    assessment: RiskAssessment | None,
    model_card: ModelCard | None,
    audit_logs: list[AuditLog],
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Rapport de conformité AI Act — {system.name}",
        author="AI Act Governance Framework",
    )

    s = _styles()
    story = []
    now = datetime.now(UTC).strftime("%d/%m/%Y à %H:%M UTC")

    # ── En-tête ──────────────────────────────────────────────────────────
    story.append(Paragraph("Rapport de conformité AI Act", s["title"]))
    story.append(Paragraph(f"Généré le {now}", s["small"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB"), spaceAfter=10))
    story.append(Spacer(1, 0.3 * cm))

    # ── Informations système ──────────────────────────────────────────────
    story.append(Paragraph("1. Informations générales", s["h1"]))
    info_data = [
        ["Nom du système", system.name],
        ["Version", system.version or "N/A"],
        ["Équipe", system.owner_team or "N/A"],
        ["Environnement", system.deployment_env or "N/A"],
        ["Statut", system.status.value],
        ["Système autonome", "Oui" if system.is_autonomous else "Non"],
        ["Affecte des personnes", "Oui" if system.affects_persons else "Non"],
    ]
    if system.use_case:
        info_data.append(["Cas d'usage", system.use_case])

    info_table = Table(info_data, colWidths=[4.5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)

    if system.tech_stack:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("Stack technologique :", s["label"]))
        story.append(Paragraph(", ".join(system.tech_stack), s["value"]))

    # ── Évaluation de risque ──────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("2. Évaluation du risque AI Act", s["h1"]))

    if not assessment:
        story.append(Paragraph("Aucune évaluation de risque effectuée.", s["body"]))
    else:
        risk_color = RISK_COLORS.get(assessment.risk_category, colors.gray)
        risk_label = RISK_LABELS.get(assessment.risk_category, str(assessment.risk_category))

        badge_table = Table([[Paragraph(risk_label, s["risk_badge"])]], colWidths=[16.5 * cm])
        badge_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), risk_color),
            ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
            ("TOPPADDING", (0, 0), (0, 0), 10),
            ("BOTTOMPADDING", (0, 0), (0, 0), 10),
            ("LEFTPADDING", (0, 0), (0, 0), 12),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]))
        story.append(badge_table)
        story.append(Spacer(1, 0.2 * cm))

        story.append(Paragraph(f"Score : {assessment.total_score} / 100", s["body"]))

        if assessment.justification:
            story.append(Paragraph("Justification :", s["label"]))
            story.append(Paragraph(assessment.justification, s["value"]))

        if assessment.ai_act_articles:
            story.append(Paragraph("Articles applicables :", s["label"]))
            story.append(Paragraph(" · ".join(assessment.ai_act_articles), s["value"]))

        if assessment.required_actions:
            story.append(Paragraph("Obligations réglementaires :", s["h2"]))
            action_data = [["Article", "Obligation", "Échéance"]]
            for action in assessment.required_actions:
                action_data.append([action["article"], action["obligation"], action.get("deadline", "N/A")])
            action_table = Table(action_data, colWidths=[3 * cm, 10 * cm, 3.5 * cm])
            action_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEF3C7")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(action_table)

    # ── Model Card ────────────────────────────────────────────────────────
    if model_card:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("3. Model Card", s["h1"]))

        sections = [
            ("Architecture", model_card.architecture),
            ("Framework", model_card.framework),
            ("Licence", model_card.license),
            ("Étapes de prétraitement", model_card.preprocessing_steps),
            ("Biais connus", model_card.known_biases),
            ("Limitations", model_card.limitations),
            ("Usages hors périmètre", model_card.out_of_scope_uses),
            ("Considérations éthiques", model_card.ethical_considerations),
            ("Mesures de conformité AI Act", model_card.conformity_measures),
            ("Supervision humaine", model_card.human_oversight),
            ("Contact DPO", model_card.dpo_contact),
        ]
        for label, value in sections:
            if value:
                story.append(Paragraph(f"{label} :", s["label"]))
                story.append(Paragraph(value, s["value"]))

        if model_card.metrics:
            story.append(Paragraph("Métriques de performance :", s["h2"]))
            metric_data = [["Métrique", "Valeur", "Dataset"]]
            for m in model_card.metrics:
                metric_data.append([m.get("name", ""), str(m.get("value", "")), m.get("dataset", "N/A")])
            metric_table = Table(metric_data, colWidths=[5 * cm, 5 * cm, 6.5 * cm])
            metric_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF6FF")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(metric_table)

    # ── Audit (dernières entrées) ─────────────────────────────────────────
    if audit_logs:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("4. Traçabilité (dernières actions)", s["h1"]))
        audit_data = [["Date", "Acteur", "Action", "Hash SHA-256"]]
        for entry in audit_logs[:10]:
            audit_data.append([
                entry.created_at.strftime("%d/%m/%Y %H:%M"),
                entry.actor_email,
                entry.action,
                entry.payload_hash[:16] + "…",
            ])
        audit_table = Table(audit_data, colWidths=[3.5 * cm, 4 * cm, 5 * cm, 4 * cm])
        audit_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(audit_table)

    # ── Pied de page ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Document généré automatiquement par AI Act Governance Framework · Confidentiel DSI",
        s["small"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
