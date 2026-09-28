from dataclasses import dataclass


@dataclass
class IncidentState:
    incident_type: str = ""
    active: bool = False
    severity: str = ""
    description: str = ""


def create_default_incident() -> IncidentState:
    return IncidentState()