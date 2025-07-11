from dataclasses import dataclass
from typing import List, Tuple
from src.models.CarbonRecord import CarbonRecord

@dataclass
class OperationalCarbonResult:
    """
    Represents the result of an operational carbon calculation.
    """
    cpu_energy: float
    cpu_energy_pue: float
    memory_energy: float
    memory_energy_pue: float
    carbon_emissions: float
    node_memory_usage: List[Tuple[float, float]]
    records: List[CarbonRecord]
