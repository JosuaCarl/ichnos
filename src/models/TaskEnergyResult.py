from dataclasses import dataclass

@dataclass
class TaskEnergyResult:
    """
    Represents the energy consumption result for a task.
    """
    core_consumption: float
    memory_consumption: float
