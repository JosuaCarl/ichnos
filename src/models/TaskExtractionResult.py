from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
from src.models.IchnosTrace import IchnosTrace
from src.models.ProcessedTrace import ProcessedTrace

@dataclass
class TaskExtractionResult:
    """
    Represents the result of extracting tasks by interval.
    """
    # Mapping of interval bucket (epoch ms) -> list of IchnosTrace tasks (possibly sliced)
    tasks_by_interval: Dict[datetime, List[IchnosTrace]]
    # All original ichnos trace records (unsliced)
    all_tasks: List[IchnosTrace]
    overhead_intervals: List[int]
    workflow_start: int
    workflow_end: int
