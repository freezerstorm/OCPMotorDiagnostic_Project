"""Conversion des lignes SQLAlchemy en dictionnaires « prêts pour l'API ».

Les routes renvoient des dictionnaires JSON simples — jamais d'objets
SQLAlchemy. Toutes les conversions sont regroupées ici (un seul endroit
à modifier si un champ est ajouté).
"""

from app.models.motor import Motor
from app.models.service import Service
from app.models.test import Measurements, Test


def _iso(dt) -> str | None:
    """Convertit une date Python en texte ISO (ou None)."""
    return dt.isoformat() if dt is not None else None


def service_to_dict(service: Service) -> dict:
    """Désignation de service → dictionnaire (clés identiques à ServiceRead)."""
    return {
        "id": service.id,
        "name": service.name,
    }


def motor_to_dict(motor: Motor) -> dict:
    """Fiche moteur → dictionnaire (clés identiques au schéma MotorRead)."""
    return {
        "motor_id": motor.motor_id,
        "matricule": motor.matricule,
        "designation": motor.designation,
        "brand": motor.brand,
        "model": motor.model,
        "serial_number": motor.serial_number,
        "rated_power_kw": motor.rated_power_kw,
        "rated_voltage_v": motor.rated_voltage_v,
        "rated_current_a": motor.rated_current_a,
        "rated_speed_rpm": motor.rated_speed_rpm,
        "cos_phi": motor.cos_phi,
        "coupling": motor.coupling,
        "service": motor.service,
        "di_ot": motor.di_ot,
        "created_at": _iso(motor.created_at),
    }


def measurements_to_dict(m: Measurements | None) -> dict:
    """Mesures → dictionnaire imbriqué (structure du schéma Measurements)."""
    if m is None:
        return {"insulation": {}, "winding": {}, "values": {}}

    return {
        "insulation": {
            "test_voltage_v": m.insulation_test_voltage_v,
            "ref_meter_insulation": m.ref_meter_insulation,
            "ph1_ph2_mohm": m.ph1_ph2_mohm,
            "ph2_ph3_mohm": m.ph2_ph3_mohm,
            "ph3_ph1_mohm": m.ph3_ph1_mohm,
            "ph1_ground_mohm": m.ph1_ground_mohm,
            "ph2_ground_mohm": m.ph2_ground_mohm,
            "ph3_ground_mohm": m.ph3_ground_mohm,
        },
        "winding": {
            "r12_ohm": m.r12_ohm,
            "r23_ohm": m.r23_ohm,
            "r31_ohm": m.r31_ohm,
            "continuity_ok": m.continuity_ok,
            "ref_meter_resistance": m.ref_meter_resistance,
        },
        "values": {
            "temperature_c": m.temperature_c,
            "temp_bearing_de_c": m.temp_bearing_de_c,
            "temp_bearing_nde_c": m.temp_bearing_nde_c,
            "ref_meter_cl": m.ref_meter_cl,
            "ref_meter_temperature": m.ref_meter_temperature,
            "supply_voltage_v": m.supply_voltage_v,
            "current_a": m.current_a,
            "vibration_mm_s": m.vibration_mm_s,
        },
    }


def test_to_dict(test: Test) -> dict:
    """Fiche de test → dictionnaire (sans le moteur imbriqué)."""
    return {
        "test_id": test.test_id,
        "mode": test.mode,
        "status": test.status,
        "decision": test.decision,
        "observation": test.observation,
        "admin": {
            "requested_by_service": test.requested_by_service,
            "notice": test.notice,
            "work_order": test.work_order,
            "received_at": test.received_at.isoformat() if test.received_at else None,
            "repair_internal": test.repair_internal,
            "repair_external": test.repair_external,
        },
        "motor_id": test.motor_id,
        "created_at": _iso(test.created_at),
        "source_ref": test.source_ref,
        "measurements": measurements_to_dict(test.measurements),
    }
