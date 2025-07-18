from dataclasses import dataclass
from typing import Dict, List

@dataclass
class TempShiftResult:
    op_carbon_results: List[str]
    emb_carbon_results: List[str]