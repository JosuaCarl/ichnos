import csv
from dataclasses import dataclass
from typing import List, Optional

from src.models.IchnosTrace import IchnosTrace

@dataclass
class ProcessedTrace:
    """Processed trace with carbon/CI metrics.

    Contains a reference to the originating UniversalTrace plus derived metrics:
      - core_kwh: dynamic energy associated with core for the task
      - mem_kwh: dynamic energy associated with memory for the task
      - average_co2e: average (or total / averaged) operational CO2e for the task
      - marginal_co2e: marginal CO2e (e.g. location / time dependent marginal intensity * energy)
      - embodied_co2e: allocated embodied emissions (hardware manufacturing amortised share)
      - avg_ci: average carbon intensity (gCO2e/kWh) used for estimation
      - ci_timeseries: filename of carbon intensity time series used (optional)

    Conversion from IchnosTrace -> ProcessedTrace will be handled by Ichnos' CO2e
    estimation strategies (not implemented here).
    """
    universal: IchnosTrace
    core_kwh: float
    mem_kwh: float
    average_co2e: float
    marginal_co2e: float
    embodied_co2e: float
    avg_ci: float
    
    average_water: float # in Liters
    avg_ewif: float
    average_land: float # in square meters
    avg_elif: float

    ci_timeseries: Optional[str] = None # filename of carbon intensity time series used (optional)


    def to_dict(self) -> dict:
        u = self.ichnos
        return {
            # IchnosTrace fields
            'id': u.id,
            'name': u.name,
            'start': u.start,
            'end': u.end,
            'cpu_count': u.cpu_count,
            'avg_cpu_usage': u.avg_cpu_usage,
            'cpu_model': u.cpu_model,
            'memory': u.memory,
            'rapl_timeseries': u.rapl_timeseries or '',
            'cpu_usage_timeseries': u.cpu_usage_timeseries or '',
            # Processed metrics
            'core_kwh': self.core_kwh,
            'mem_kwh': self.mem_kwh,
            'average_co2e': self.average_co2e,
            'marginal_co2e': self.marginal_co2e,
            'embodied_co2e': self.embodied_co2e,
            'avg_ci': self.avg_ci,
            'ci_timeseries': self.ci_timeseries or ''
        }

    @staticmethod
    def fieldnames() -> List[str]:
        return [
            'id','name','start','end','cpu_count','avg_cpu_usage','cpu_model','memory',
            'rapl_timeseries','cpu_usage_timeseries','core_kwh','mem_kwh',
            'average_co2e','marginal_co2e','embodied_co2e','avg_ci','ci_timeseries'
        ]

    @staticmethod
    def to_csv(traces: List['ProcessedTrace'], filepath: str):
        """Write processed traces to CSV (always writes header)."""
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=ProcessedTrace.fieldnames())
            writer.writeheader()
            for t in traces:
                writer.writerow(t.to_dict())
