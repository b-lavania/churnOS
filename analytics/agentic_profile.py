"""
Agentic Product Profile — ontology switch + generator priors.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

PRESETS: dict[str, dict[str, Any]] = {
    "assistant_heavy": {
        "preset_id": "assistant_heavy",
        "label": "Personal assistant — inbox & calendar",
        "ontology_vertical": "agent_runtime",
        "ontology_version": "agent_runtime_v1",
        "billing_model": "b2b_subscription",
        "default_model": "gpt-4o",
        "max_loops_threshold": 8,
        "cache_hit_rate": 0.7,
        "description": "Seats delegate email and calendar work. High approval volume; retention hinges on weekly habit, not one-off runs.",
        "priors": {
            "n_seats": 800,
            "n_capabilities": 12,
            "activation_rate": 0.62,
            "weekly_habit_rate": 0.48,
            "approval_fatigue_rate": 0.22,
            "trust_incident_rate": 0.04,
            "connector_error_rate": 0.08,
            "run_cost_per_success": 0.35,
            "seat_arpu_monthly": 49.99,
            "monthly_churn_base": 0.06,
            "revenue_per_1k_tokens": 0.02,
        },
    },
    "workspace_crm": {
        "preset_id": "workspace_crm",
        "label": "CRM workspace — pipeline automations",
        "ontology_vertical": "capability_lifecycle",
        "ontology_version": "capability_lifecycle_v1",
        "billing_model": "b2b_subscription",
        "default_model": "claude-3-5-sonnet",
        "max_loops_threshold": 10,
        "cache_hit_rate": 0.65,
        "description": "Overnight deal-pipeline agents wired to CRM tools. Connector depth and overnight-run reliability drive value.",
        "priors": {
            "n_seats": 1200,
            "n_capabilities": 18,
            "activation_rate": 0.55,
            "weekly_habit_rate": 0.52,
            "approval_fatigue_rate": 0.18,
            "trust_incident_rate": 0.03,
            "connector_error_rate": 0.12,
            "run_cost_per_success": 0.55,
            "seat_arpu_monthly": 79.0,
            "monthly_churn_base": 0.05,
            "revenue_per_1k_tokens": 0.025,
        },
    },
    "ops_mission": {
        "preset_id": "ops_mission",
        "label": "Ops missions — docs & escalations",
        "ontology_vertical": "capability_lifecycle",
        "ontology_version": "capability_lifecycle_v1",
        "billing_model": "b2b_subscription",
        "default_model": "gpt-4o",
        "max_loops_threshold": 12,
        "cache_hit_rate": 0.55,
        "description": "Multi-step back-office missions through document portals. Escalation-heavy; trust and approval friction are the risk.",
        "priors": {
            "n_seats": 400,
            "n_capabilities": 10,
            "activation_rate": 0.48,
            "weekly_habit_rate": 0.38,
            "approval_fatigue_rate": 0.28,
            "trust_incident_rate": 0.06,
            "connector_error_rate": 0.15,
            "run_cost_per_success": 0.85,
            "seat_arpu_monthly": 129.0,
            "monthly_churn_base": 0.07,
            "revenue_per_1k_tokens": 0.03,
        },
    },
    "api_metered": {
        "preset_id": "api_metered",
        "label": "Metered agent API — usage-priced",
        "ontology_vertical": "agent_runtime",
        "ontology_version": "agent_runtime_v1",
        "billing_model": "usage_based",
        "default_model": "gpt-4o-mini",
        "max_loops_threshold": 8,
        "cache_hit_rate": 0.6,
        "description": "Usage-priced agent API where inference volume is revenue, not only COGS. Margins track successful outcomes per dollar of spend.",
        "priors": {
            "n_seats": 600,
            "n_capabilities": 10,
            "activation_rate": 0.58,
            "weekly_habit_rate": 0.5,
            "approval_fatigue_rate": 0.15,
            "trust_incident_rate": 0.035,
            "connector_error_rate": 0.09,
            "run_cost_per_success": 0.4,
            "seat_arpu_monthly": 0.0,
            "monthly_churn_base": 0.08,
            "revenue_per_1k_tokens": 0.04,
        },
    },
}


def get_preset(preset_id: str) -> dict[str, Any]:
    if preset_id not in PRESETS:
        raise KeyError(f"Unknown preset: {preset_id}")
    return deepcopy(PRESETS[preset_id])


def list_presets() -> list[str]:
    return list(PRESETS.keys())
