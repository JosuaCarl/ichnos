from dataclasses import dataclass

@dataclass
class IchnosResult:
    """
    Represents the final result of an Ichnos carbon footprint calculation.
    """
    summary: str
    operational_emissions: float
    embodied_emissions: float
