from src.external_apis.Boavizta import get_cpu_impact
from src.models.CarbonRecord import CarbonRecord

from typing import List
import sys

DEFAULT_CPU_LIFETIME = 5.0 * 365.25 * 24  # 5 years in hours

def calculate_cpu_embodied_carbon(cpu_model: str, duration_used: float, lifetime: float = None, cpu_usage: float = 1.0) -> float:
    """
    Calculate the embodied carbon for a CPU model based on its usage duration and expected lifetime. Currently assumes 100% CPU utilisation of all cores.
    
    Parameters:
    cpu_model (str): The model of the CPU.
    duration_used (float): The duration the CPU has been used in time units; only used as a ratio so units don't matter, unless no lifetime is provided, then the unit has to be hours.
    lifetime (float): The expected lifetime of the CPU in time units. If None, defaults to 5 years (in hours).
    cpu_usage (float): The percentage of CPU usage (0.0 to 1.0). Defaults to 1.0 (100% usage).
    
    Returns:
    float: The estimated embodied carbon in grams.
    """
    
    cpu_lca = get_cpu_impact(cpu_model)
    if lifetime is None:
        lifetime = DEFAULT_CPU_LIFETIME
    embodied_carbon_kg = cpu_lca * (duration_used / lifetime)
    embodied_carbon_kg *= cpu_usage  # Adjust for CPU usage
    return embodied_carbon_kg * 1000  # Convert to grams

def embodied_carbon_for_carbon_records(records: List[CarbonRecord], use_cpu_usage: bool = False) -> float:
    """
	Calculate the embodied carbon for a list of CarbonRecord objects.
	
	Parameters:
	records (List[CarbonRecord]): A list of CarbonRecord objects.
	use_cpu_usage (bool): Flag to indicate whether to consider CPU usage in calculations.
	
	Returns:
	float: The total embodied carbon in kilograms.
	"""
	
    total_embodied_carbon = 0.0
    for record in records:
        cpu_model = record.cpu_model
        duration_used = record.realtime / 1000 / 3600  # convert from ms to hours
        adjusted_cpu_usage = 1.0
        if use_cpu_usage:
            # Adjust CPU usage percent based on the number of cores
            adjusted_cpu_usage = record.cpu_usage / (record.core_count * 100)
        
        total_embodied_carbon += calculate_cpu_embodied_carbon(cpu_model, duration_used, cpu_usage=adjusted_cpu_usage)
    
    return total_embodied_carbon

if __name__ == "__main__":
    # Parse args
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: python calculate_cpu_embodied_carbon.py <cpu_model> <duration_used> [lifetime]")
        sys.exit(1)
  
    cpu_model = args[0]
    duration_used = float(args[1])
    lifetime = float(args[2]) if len(args) > 2 else None
    
    embodied_carbon = calculate_cpu_embodied_carbon(cpu_model, duration_used, lifetime)
    print(f"Estimated embodied carbon for {cpu_model} used for {duration_used} hours: {embodied_carbon:.2f} g CO2e")
    