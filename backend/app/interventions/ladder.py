from __future__ import annotations

LADDER = {
    "green": {"response": "self_help", "actor": "app", "sla_hours": None, "catalogue": []},
    "amber": {
        "response": "buddy_jco_informal",
        "actor": "buddy+jco",
        "sla_hours": 72,
        "catalogue": ["INT-BUDDY", "INT-ROSTER", "INT-LEAVE", "INT-FAMILY"],
    },
    "red": {
        "response": "counsellor_outreach",
        "actor": "counsellor",
        "sla_hours": 24,
        "catalogue": ["INT-COUNSEL", "INT-TELEMANAS", "INT-ROSTER", "INT-LEAVE", "INT-FAMILY"],
    },
    "critical": {
        "response": "immediate_contact_duty_mod",
        "actor": "counsellor+welfare_officer",
        "sla_hours": 0,
        "catalogue": ["INT-COUNSEL", "INT-TELEMANAS", "INT-ROSTER"],
    },
}

SLA = {"green": None, "amber": 72, "red": 24, "critical": 0}
