from dataclasses import dataclass
from typing import Dict, List
from src.models.CarbonRecord import CarbonRecord

@dataclass
class TasksByTimeResult:
    """
    Represents the result of grouping tasks by a time interval, including overheads.
    """
    tasks_by_time: Dict[int, List[CarbonRecord]]
    overheads: List[int]
