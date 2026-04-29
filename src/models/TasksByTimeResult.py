from dataclasses import dataclass
from typing import Dict, List
from src.models.IchnosTrace import IchnosTrace

@dataclass
class TasksByTimeResult:
    """
    Represents the result of grouping tasks by a time interval, including overheads.
    """
    tasks_by_time: Dict[int, List[IchnosTrace]]
    overheads: List[int]
