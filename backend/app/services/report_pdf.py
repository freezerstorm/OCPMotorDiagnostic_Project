"""Génération du RAPPORT PDF d'un diagnostic — É19 « FICHE D'ESSAI MOTEUR ».

Le PDF est la PREUVE DOCUMENTAIRE du test (§16-17) : il reprend la
structure de la fiche papier OCP « FICHE D'ESSAI MOTEUR » :

    En-tête            logo · titre · n° de diagnostic · date · version
    Identification     plaque signalétique + service + DI/OT
    Isolement          table Mesure | mesure | unité | Valeur Réf | Observation
    Résistances        R12/R23/R31 + « Continuité des enroulements : Oui/Non »
    Tension / courant  courant à vide I0 (limites In/3 – 2In/3)
    Température        2 paliers (limite < 70 °C) ; valeur unique ancienne
    Vibration          valeur enregistrée (règle non définie à ce jour)
    Observations       observation du technicien
    Zone admin         Sce demandeur · AVIS · ORDRE · réception · réparations
    Décision           « Équipement conforme : Oui/Non » + décision + visa

L'INTERPRÉTATION (causes possibles, risques, recommandations,
conclusion générale) reste sur la page ANALYSE : le rapport n'en est
PAS une copie. Chaque ligne porte seulement son évaluation de règle
(conforme / problématique / critique), calculée par les modules de
`diagnostic_rules/` — rien n'est inventé.

Bibliothèque : ReportLab (PDF sans composant système externe).
"""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# --- Couleurs de marque (identiques au thème du frontend) ---
OCP_GREEN = colors.HexColor("#2b843d")
OCP_GREEN_DEEPER = colors.HexColor("#175225")
OCP_SOFT = colors.HexColor("#e9f3ec")
TEXT_GREY = colors.HexColor("#5b6b60")
BORDER = colors.HexColor("#d8e3da")

# Logo de marque (fichier interne, remplaçable sans toucher au code)
_LOGO_PATH = (
    Path(__file__).resolve().parents[3] / "frontend" / "public" / "brand" / "ocp-emblem.png"
)

# Version du document (affichée en en-tête, comme « Version 02 » sur le papier)
_DOC_VERSION = "0.18"

# --- Polices : DejaVu (accents + symboles) si présente, sinon Helvetica ---
_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"

try:
    _dejavu = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("OCP", str(_dejavu / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("OCP-Bold", str(_dejavu / "DejaVuSans-Bold.ttf")))
    _FONT, _FONT_BOLD = "OCP", "OCP-Bold"
except Exception:  # pragma: no cover — repli si les TTF sont absentes
    pass

# Libellés français (codes machine du backend)
_DECISION_LABELS = {"serviced": "REMIS EN SERVICE", "repair": "ENVOYÉ EN RÉPARATION"}
_MODE_LABELS = {"manual": "Test manuel", "auto": "Test automatique (kit)"}


def _v(value, suffix: str = "") -> str:
    """Valeur lisible : nombre tel quel + unité, ou « — » si absent."""
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        value = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value}{suffix}"


def _rmin_text(voltage_v) -> str:
    """Résistance minimale requise lisible : Rmin = Vtest × 1 kΩ."""
    if voltage_v is None:
        return "—"
    rmin_mohm = voltage_v / 1000
    if rmin_mohm >= 1:
        return f"{rmin_mohm:g} MΩ"
    return f"{rmin_mohm * 1000:g} kΩ"


def _styles() -> dict:
    """Styles de texte du document."""
    return {
        "title": ParagraphStyle("title", fontName=_FONT_BOLD, fontSize=14,
                                textColor=OCP_GREEN_DEEPER, leading=18),
        "code": ParagraphStyle("code", fontName=_FONT, fontSize=8,
                               textColor=TEXT_GREY, leading=11),
        "subtitle": ParagraphStyle("subtitle", fontName=_FONT, fontSize=8.5,
                                   textColor=TEXT_GREY, leading=12),
        "section": ParagraphStyle("section", fontName=_FONT_BOLD, fontSize=10,
                                  textColor=colors.white, leading=13),
        "line": ParagraphStyle("line", fontName=_FONT, fontSize=9,
                               textColor=colors.HexColor("#1c2b22"), leading=13),
        "big": ParagraphStyle("big", fontName=_FONT_BOLD, fontSize=11,
                              textColor=OCP_GREEN_DEEPER, leading=15),
        "muted": ParagraphStyle("muted", fontName=_FONT, fontSize=8,
                                textColor=TEXT_GREY, leading=11),
        "cell": ParagraphStyle("cell", fontName=_FONT, fontSize=8.5,
                               textColor=colors.HexColor("#1c2b22"), leading=11),
        "cellb": ParagraphStyle("cellb", fontName=_FONT_BOLD, fontSize=8.5,
                                textColor=TEXT_GREY, leading=11),
    }


def _section(story: list, number: int, title: str, styles: dict) -> None:
    """Bandeau vert d'un titre de rubrique."""
    table = Table(
        [[Paragraph(f"{number}.  {title}", styles["section"])]],
        colWidths=[182 * mm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), OCP_GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([Spacer(1, 4 * mm), table, Spacer(1, 2.5 * mm)])


def _kv_table(rows: list, widths: list | None = None) -> Table:
    """Petit tableau « libellé : valeur »."""
    data = [[Paragraph(f"<b>{k}</b>", ParagraphStyle(
                "k", fontName=_FONT_BOLD, fontSize=9, textColor=TEXT_GREY, leading=12)),
             Paragraph(str(v), ParagraphStyle(
                "val", fontName=_FONT, fontSize=9, leading=12))]
            for k, v in rows]
    table = Table(data, colWidths=widths or [58 * mm, 124 * mm])
    table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, OCP_SOFT]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _measure_table(rows: list) -> Table:
    """Table de mesures type fiche papier :
    Mesure | mesure | unité | Valeur Réf | Observation."""
    header = ["Mesure", "mesure", "unité", "Valeur Réf", "Observation"]
    data = [[Paragraph(f"<b>{h}</b>", ParagraphStyle(
                "h", fontName=_FONT_BOLD, fontSize=8.5,
                textColor=colors.white, leading=11)) for h in header]]
    for label, value, unit, ref, obs in rows:
        data.append([
            Paragraph(str(label), ParagraphStyle("c0", parent=_cell_style(), fontName=_FONT_BOLD)),
            Paragraph(str(value), _cell_style()),
            Paragraph(str(unit), _cell_style()),
            Paragraph(str(ref), _cell_style()),
            Paragraph(str(obs), _cell_style()),
        ])
    table = Table(data, colWidths=[52 * mm, 30 * mm, 16 * mm, 38 * mm, 46 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), OCP_GREEN_DEEPER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, OCP_SOFT]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _cell_style() -> ParagraphStyle:
    return ParagraphStyle("cell", fontName=_FONT, fontSize=8.5,
                          textColor=colors.HexColor("#1c2b22"), leading=11)


def _result_by_parameter(analysis: dict, parameter: str) -> dict | None:
    """Résultat d'analyse d'UN paramètre (ou None)."""
    return next((r for r in analysis["results"] if r["parameter"] == parameter), None)


def _item_by_key(result: dict | None, key: str) -> dict | None:
    """Sous-résultat d'une mesure (items d'isolement / de paliers)."""
    if not result:
        return None
    return next((i for i in (result.get("items") or []) if i.get("key") == key), None)


def _footer(canvas, doc) -> None:
    """Pied de page : traçabilité du document + numéro de page."""
    canvas.saveState()
    canvas.setFont(_FONT, 7.5)
    canvas.setFillColor(TEXT_GREY)
    canvas.drawString(
        14 * mm, 9 * mm,
        "OCP Motor Diagnostic — fiche générée automatiquement à partir des données enregistrées",
    )
    canvas.drawRightString(196 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_report_pdf(test, samples: list[dict], analysis: dict) -> bytes:
    """Construit la FICHE D'ESSAI MOTEUR PDF et renvoie les octets."""
    motor = test.motor
    m = test.measurements
    styles = _styles()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=16 * mm,
        title=f"Fiche d'essai moteur {test.test_id}",
        author="OCP Motor Diagnostic",
    )

    # ===== En-tête (esprit fiche papier : logo · titre · bloc document) =====
    logo = Image(str(_LOGO_PATH), width=15 * mm, height=15 * mm) if _LOGO_PATH.is_file() else ""
    code_block = [
        Paragraph("Généré par l'application", styles["code"]),
        Paragraph(f"Version {_DOC_VERSION}", styles["code"]),
        Paragraph(f"Diagnostic {test.test_id}", styles["code"]),
    ]
    head = Table(
        [[logo,
          Paragraph("FICHE D'ESSAI MOTEUR", styles["title"]),
          code_block]],
        colWidths=[20 * mm, 122 * mm, 40 * mm],
    )
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 1, OCP_GREEN),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    date_essai = test.created_at.strftime("%d/%m/%Y") if test.created_at else "—"
    story = [
        head,
        Spacer(1, 2 * mm),
        Paragraph(
            f"<b>Date d'essai :</b> {date_essai}   ·   "
            f"<b>Mode :</b> {_MODE_LABELS.get(test.mode, test.mode)}",
            styles["subtitle"],
        ),
    ]

    # ===== 1. Identification du moteur =====
    _section(story, 1, "Identification du moteur", styles)
    story.append(_kv_table([
        ("Matériel / Désignation", _v(motor.designation if motor else None)),
        ("Matricule", _v((motor.matricule if motor else None) or (motor.motor_id if motor else None))),
        ("Marque / Modèle", _v(motor.brand if motor else None) + " / " + _v(motor.model if motor else None)),
        ("N° de fabrication", _v(motor.serial_number if motor else None)),
        ("Puissance P", _v(motor.rated_power_kw if motor else None, " kW")),
        ("Tension U", _v(motor.rated_voltage_v if motor else None, " V")),
        ("Courant nominal In", _v(motor.rated_current_a if motor else None, " A")),
        ("Vitesse N (plaque)", _v(motor.rated_speed_rpm if motor else None, " tr/min")),
        ("Cos φ", _v(motor.cos_phi if motor else None)),
        ("Couplage", _v(motor.coupling if motor else None)),
        ("Service / Environnement", _v(motor.service if motor else None)),
        ("DI / OT", _v(motor.di_ot if motor else None)),
    ]))

    # ===== 2. Mesure d'isolement =====
    _section(story, 2, "Mesure d'isolement", styles)
    insulation = _result_by_parameter(analysis, "insulation")
    ref_meter_iso = m.ref_meter_insulation if m else None
    story.append(Paragraph(
        f"<b>Réf. appareil de mesure :</b> {_v(ref_meter_iso)}   ·   "
        f"<b>Tension d'essai :</b> {_v(m.insulation_test_voltage_v if m else None, ' V')}   ·   "
        f"<b>Rmin (1 kΩ/V) :</b> {_rmin_text(m.insulation_test_voltage_v if m else None)}",
        styles["line"]))
    story.append(Spacer(1, 1.5 * mm))
    iso_rows = []
    for key, label in (
        ("ph1_ph2", "Ph1–Ph2"), ("ph2_ph3", "Ph2–Ph3"), ("ph3_ph1", "Ph3–Ph1"),
        ("ph1_ground", "Ph1–Masse"), ("ph2_ground", "Ph2–Masse"), ("ph3_ground", "Ph3–Masse"),
    ):
        item = _item_by_key(insulation, key)
        raw = getattr(m, f"{key}_mohm", None) if m else None
        value = _v(raw, " MΩ")
        ref = _rmin_text(m.insulation_test_voltage_v if m else None)
        if item:
            obs = item["evaluation_label"]
        else:
            obs = "non mesurée"
        iso_rows.append((label, value, "MΩ", ref, obs))
    story.append(_measure_table(iso_rows))

    # ===== 3. Mesure des résistances =====
    _section(story, 3, "Mesure des résistances", styles)
    winding = _result_by_parameter(analysis, "winding_resistance")
    story.append(Paragraph(
        f"<b>Réf. appareil de mesure :</b> {_v(m.ref_meter_resistance if m else None)}",
        styles["line"]))
    story.append(Spacer(1, 1.5 * mm))
    if winding and winding["evaluation"] != "non_evaluable":
        wind_obs = winding["interpretation"]
    else:
        wind_obs = "non évaluée (mesures incomplètes)"
    wind_rows = [
        ("R12", _v(m.r12_ohm if m else None, " Ω"), "Ω", "—", wind_obs),
        ("R23", _v(m.r23_ohm if m else None, " Ω"), "Ω", "—", ""),
        ("R31", _v(m.r31_ohm if m else None, " Ω"), "Ω", "—", ""),
    ]
    story.append(_measure_table(wind_rows))
    story.append(Spacer(1, 1.5 * mm))
    continuity_text = "—"
    if m is not None and m.continuity_ok is not None:
        continuity_text = "Oui" if m.continuity_ok else "Non"
    story.append(Paragraph(
        f"<b>Continuité des enroulements :</b> {continuity_text}   "
        f"<font size=8 color='#5b6b60'>(appréciation globale du technicien)</font>",
        styles["line"]))

    # ===== 4. Mesure tension / courant =====
    _section(story, 4, "Mesure tension / courant", styles)
    current = _result_by_parameter(analysis, "current_no_load")
    story.append(Paragraph(
        f"<b>Réf. appareil (pince tension/courant) :</b> {_v(m.ref_meter_cl if m else None)}   ·   "
        f"<b>Courant nominal In :</b> {_v(motor.rated_current_a if motor else None, ' A')}",
        styles["line"]))
    story.append(Paragraph(
        f"<b>Tension d'alimentation :</b> {_v(m.supply_voltage_v if m else None, ' V')}",
        styles["line"]))
    story.append(Spacer(1, 1.5 * mm))
    if current and current["evaluation"] != "non_evaluable":
        d = current["display"]
        i0_ref = f"In/3 < I0 < 2In/3  ({_v(d.get('limit_min_a'), '')} – {_v(d.get('limit_max_a'), '')} A)"
        i0_obs = current["evaluation_label"]
    else:
        i0_ref = "In/3 < I0 < 2In/3"
        i0_obs = "non évaluable (In ou I0 manquante)"
    story.append(_measure_table([
        ("Courant à vide I0", _v(m.current_a if m else None, " A"), "A", i0_ref, i0_obs),
    ]))

    # ===== 5. Mesure température (paliers) =====
    _section(story, 5, "Mesure température (paliers)", styles)
    story.append(Paragraph(
        f"<b>Réf. appareil (température) :</b> {_v(m.ref_meter_temperature if m else None)}   ·   "
        f"<b>Limite par palier :</b> &lt; 70 °C",
        styles["line"]))
    story.append(Spacer(1, 1.5 * mm))
    temperature = _result_by_parameter(analysis, "temperature")
    temp_rows = []
    for key, label in (("de", "Palier côté accouplement"), ("nde", "Palier C.O.A (côté opposé)")):
        raw = getattr(m, f"temp_bearing_{key}_c", None) if m else None
        item = _item_by_key(temperature, key)
        obs = item["evaluation_label"] if item else "non mesurée"
        temp_rows.append((label, _v(raw, " °C"), "°C", "&lt; 70", obs))
    if m is not None and m.temperature_c is not None:
        legacy_obs = "CRITIQUE (≥ 85)" if m.temperature_c >= 85 else "NON CRITIQUE (&lt; 85)"
        temp_rows.append((
            "Température unique (ancien format)",
            _v(m.temperature_c, " °C"), "°C", "&lt; 85", legacy_obs,
        ))
    story.append(_measure_table(temp_rows))

    # ===== 6. Vibration =====
    _section(story, 6, "Vibration", styles)
    if samples:
        duration = samples[-1]["t_s"] - samples[0]["t_s"]
        extra = f" — acquisition kit : {len(samples)} échantillons sur {duration:.1f} s"
    else:
        extra = ""
    story.append(_measure_table([
        ("Vibration", _v(m.vibration_mm_s if m else None, " mm/s"), "mm/s",
         "—", "enregistrée (règle non définie à ce jour)" + extra),
    ]))

    # ===== 7. Observation du technicien =====
    _section(story, 7, "Observation du technicien", styles)
    story.append(Paragraph(test.observation or "—", styles["line"]))

    # ===== 8. Zone administrative (fiche papier) =====
    _section(story, 8, "Zone administrative", styles)
    story.append(_kv_table([
        ("Sce demandeur", _v(test.requested_by_service)),
        ("AVIS", _v(test.notice)),
        ("ORDRE", _v(test.work_order)),
        ("Date de réception",
         test.received_at.strftime("%d/%m/%Y") if test.received_at else "—"),
        ("Réparation interne",
         "—" if test.repair_internal is None else ("Oui" if test.repair_internal else "Non")),
        ("Réparation externe",
         "—" if test.repair_external is None else ("Oui" if test.repair_external else "Non")),
    ]))

    # ===== 9. Équipement conforme + décision finale =====
    _section(story, 9, "Équipement conforme / Décision finale", styles)
    oui = "X" if test.decision == "serviced" else " "
    non = "X" if test.decision == "repair" else " "
    decision_line = _DECISION_LABELS.get(test.decision) if test.decision else "Non enregistrée à ce jour."
    date_visa = test.created_at.strftime("%d/%m/%Y") if test.created_at else "—"
    story.append(_kv_table([
        ("Équipement conforme", f"[ {oui} ]  Oui          [ {non} ]  Non"),
        ("Décision finale", decision_line),
        ("Date", date_visa),
        ("Visa / technicien", "____________________"),
    ]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "L'interprétation détaillée (causes possibles, risques, recommandations) figure "
        "sur la page ANALYSE de l'application — le présent rapport fait foi sur les "
        "valeurs mesurées et leurs évaluations de règles.",
        styles["muted"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
