from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
from src.models.CarbonRecord import CarbonRecord
from src.models.TraceRecord import TraceRecord

@dataclass
class TaskExtractionResult:
    """
    Represents the result of extracting tasks by interval.
    """
    tasks_by_interval: Dict[datetime, List[CarbonRecord]]
    all_tasks: List[CarbonRecord]
    trace_records: List[TraceRecord]
    overhead_intervals: List[int]
    workflow_start: int
    workflow_end: int
