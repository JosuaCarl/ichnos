import sys

from src.models.CarbonRecord import CarbonRecord
from src.Constants import *
from src.utils.Parsers import parse_arguments, parse_ci_intervals
from src.utils.TimeUtils import extract_tasks_by_hour, to_timestamp
from src.utils.FileWriters import write_trace_and_detailed_report, write_summary_file

# Functions
def linear_power_model(cpu_usage, min_watts, max_watts):
    return min_watts + cpu_usage * (max_watts - min_watts)

# Estimate Energy Consumption using CCF Methodology
def estimate_task_energy_consumption_ccf(task: CarbonRecord, min_watts, max_watts, memory_coefficient):
    # Time (h)
    time = task.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = task.get_core_count()
    # CPU Usage (%)
    cpu_usage = task.get_cpu_usage() / (100.0 * no_cores)
    # Memory (GB)
    memory = task.get_memory() / 1073741824  # memory reported in bytes  https://www.nextflow.io/docs/latest/metrics.html 
    # Core Energy Consumption (without PUE)
    core_consumption = time * linear_power_model(cpu_usage, min_watts, max_watts) * 0.001  # convert from W to kW
    # Memory Power Consumption (without PUE)
    memory_consumption = memory * memory_coefficient * time * 0.001  # convert from W to kW
    # Overall and Memory Consumption (kWh) (without PUE)
    return (core_consumption, memory_consumption)


# Estimate Carbon Footprint using CCF Methodology
def calculate_carbon_footprint_ccf(tasks_by_hour, ci, pue: float, min_watts, max_watts, memory_coefficient, check_node_memory=False):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0
    records = []
    node_memory_used = []

    for hour, tasks in tasks_by_hour.items():
        if len(tasks) > 0:
            if isinstance(ci, float):
                ci_val = ci
            else:
                hour_ts = to_timestamp(hour)
                hh = str(hour_ts.hour).zfill(2)
                month = str(hour_ts.month).zfill(2)
                day = str(hour_ts.day).zfill(2)
                mm = str(hour_ts.minute).zfill(2)
                ci_key = f'{month}/{day}-{hh}:{mm}'
                ci_val = ci[ci_key] 

            if check_node_memory:
                starts = []
                ends = []

                for task in tasks:
                    starts.append(int(task.get_start()))
                    ends.append(int(task.get_complete()))

                earliest = min(starts)
                latest = max(ends)
                realtime = (latest - earliest) / 1000 / 3600  # convert from ms to h 
                node_memory_used.append((realtime, ci_val))

            for task in tasks:
                (energy, memory) = estimate_task_energy_consumption_ccf(task, min_watts, max_watts, memory_coefficient)
                energy_pue = energy * pue
                memory_pue = memory * pue
                task_footprint = (energy_pue + memory_pue) * ci_val
                task.set_energy(energy_pue)
                task.set_co2e(task_footprint)
                task.set_avg_ci(ci_val)
                total_energy += energy
                total_energy_pue += energy_pue
                total_memory_energy += memory
                total_memory_energy_pue += memory_pue
                total_carbon_emissions += task_footprint
                records.append(task)

    return ((total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions, node_memory_used), records)

def main(arguments):
    # Data
    workflow = arguments[TRACE]
    pue = arguments[PUE]

    if MIN_WATTS in arguments and MAX_WATTS in arguments:
        min_watts = arguments[MIN_WATTS]
        max_watts = arguments[MAX_WATTS]

    memory_coefficient = arguments[MEMORY_COEFFICIENT]
    (tasks_by_hour, _) = extract_tasks_by_hour(workflow)

    summary = ""
    summary += "Carbon Footprint Trace:\n"
    summary += f"- carbon-intensity: {arguments[CI]}\n"
    summary += f"- power-usage-effectiveness: {pue}\n"
    summary += f"- min to max watts: {min_watts}W to {max_watts}W\n"
    summary += f"- memory-power-draw: {memory_coefficient}\n"

    if isinstance(arguments[CI], float):
        ci = arguments[CI]
    else:
        ci_filename = f"data/intensity/{arguments[CI]}.{FILE}"
        ci = parse_ci_intervals(ci_filename)

    check_reserved_memory_flag = RESERVED_MEMORY in arguments

    (cf, records) = calculate_carbon_footprint_ccf(tasks_by_hour, ci, pue, min_watts, max_watts, memory_coefficient, check_reserved_memory_flag)
    cpu_energy, cpu_energy_pue, mem_energy, mem_energy_pue, carbon_emissions, node_memory_usage = cf

    summary += "\nCloud Carbon Footprint Method:\n"
    summary += f"- Energy Consumption (exc. PUE): {cpu_energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {cpu_energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {mem_energy}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {mem_energy_pue}kWh\n"
    summary += f"- Carbon Emissions: {carbon_emissions}gCO2e"

    print(f"Carbon Emissions: {carbon_emissions}gCO2e")

    if check_reserved_memory_flag:
        total_res_mem_energy = 0
        total_res_mem_emissions = 0

        for realtime, ci_val in node_memory_usage:
            res_mem_energy = (arguments[RESERVED_MEMORY] * memory_coefficient * realtime * 0.001) * arguments[NUM_OF_NODES]  # convert from W to kW
            total_res_mem_energy += res_mem_energy
            total_res_mem_emissions += res_mem_energy * ci_val

        total_energy = total_res_mem_energy + cpu_energy + mem_energy
        res_report = f"Reserved Memory Energy Consumption: {total_res_mem_energy}kWh"
        res_ems_report = f"Reserved Memory Carbon Emissions: {total_res_mem_emissions}gCO2e"
        energy_split_report = f"% CPU [{((cpu_energy / total_energy) * 100):.2f}%] | % Memory [{(((total_res_mem_energy + mem_energy) / total_energy) * 100):.2f}%]"
        summary += f"\n{res_report}\n"
        summary += f"{res_ems_report}\n"
        summary += f"{energy_split_report}\n"
        print(res_report)
        print(energy_split_report)

    if TASK_FLAG:
        time = 0

        for _, tasks in tasks_by_hour.items():
            for task in tasks:
                time += task.get_realtime()

        hours = time
        summary += f"\nTask Runtime: {hours}ms\n"


    # Report Summary
    if isinstance(ci, float):
        ci = str(int(ci))
    else:
        ci = arguments[CI]

    write_summary_file("output", workflow + "-" + ci, summary)
    write_trace_and_detailed_report("output", workflow + "-" + ci, records, summary)

    return (summary, carbon_emissions)


def get_carbon_footprint(command):
    arguments = parse_arguments(command.split(' '))
    return main(arguments)


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    args = sys.argv[1:]
    arguments = parse_arguments(args)
    main(arguments)
