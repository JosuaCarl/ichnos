from dataclasses import dataclass, field
from typing import Any, Optional

HEADERS = "name,id,co2e,energy,avg_ci,realtime,cpu_model,cpu_count,cpu_powerdraw,cpu_usage,memory,memory_powerdraw"

@dataclass(unsafe_hash=True)
class CarbonRecord:
    energy: Optional[float]
    co2e: Optional[float]
    id: Any
    realtime: float
    start: Optional[Any] = None
    complete: Optional[Any] = None
    core_count: int = 0
    cpu_powerdraw: Optional[float] = None
    cpu_usage: float = 0.0
    cpu_model: str = ""
    memory: Optional[float] = None
    name: str = ""
    avg_ci: Optional[float] = None
    memory_powerdraw: Optional[float] = field(default=None, repr=False)
    
    def __str__(self) -> str:
        return f"{self.name},{self.id},{self.co2e},{self.energy},{self.avg_ci},{self.realtime},"\
               f"{self.cpu_model},{self.core_count},{self.cpu_powerdraw},{self.cpu_usage},{self.memory},{self.memory_powerdraw}"
