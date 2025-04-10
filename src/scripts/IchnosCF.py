from typing import Any, Dict, List, Tuple
from src.utils.TimeUtils import to_timestamp, extract_tasks_by_interval
from src.utils.Parsers import parse_ci_intervals, parse_arguments
from src.utils.FileWriters import write_summary_file, write_task_trace_and_rank_report
from src.Constants import *
from src.scripts.OperationalCarbon import calculate_carbon_footprint_ccf
from src.scripts.EmbodiedCarbon import embodied_carbon_for_carbon_records

import sys

def main(arguments: Dict[str, Any]) -> Tuple[str, float]:
    """
    Main function to compute and report the carbon footprint.
    
    :param arguments: Argument dictionary parsed from command line.
    :return: A tuple of (summary string, carbon emissions).
    """
    # TODO: Revise this default value (this is for GPG Node 13 OnDemand)
    default_node_mem_draw: float = 0.40268229166666664

    # Data
    workflow: str = arguments[TRACE]
    pue: float = arguments[PUE]
    interval: int = arguments[INTERVAL]
    model_name: str = arguments[MODEL_NAME]
    memory_coefficient: float = default_node_mem_draw

    if memory_coefficient is None:
        memory_coefficient = DEFAULT_MEMORY_POWER_DRAW

    tasks_by_interval, _ = extract_tasks_by_interval(workflow, interval)

    for curr_interval, records_list in tasks_by_interval.items():
        print(f'interval: {to_timestamp(curr_interval)}')
        if records_list:
            print(f'tasks: {", ".join([record.id for record in records_list])}')

    summary: str = ""
    summary += "Carbon Footprint Trace:\n"
    summary += f"- carbon-intensity: {arguments[CI]}\n"
    summary += f"- power-usage-effectiveness: {pue}\n"
    summary += f"- power model selected: {model_name}\n"
    summary += f"- memory-power-draw: {memory_coefficient}\n"

    if isinstance(arguments[CI], float):
        ci = arguments[CI]
    else:
        ci_filename: str = f"data/intensity/{arguments[CI]}.{FILE}"
        ci = parse_ci_intervals(ci_filename)

    check_reserved_memory_flag: bool = RESERVED_MEMORY in arguments

    cf, records_res = calculate_carbon_footprint_ccf(tasks_by_interval, ci, pue, model_name, memory_coefficient, check_reserved_memory_flag)
    cpu_energy, cpu_energy_pue, mem_energy, mem_energy_pue, op_carbon_emissions, node_memory_usage = cf

    emb_carbon_emissions = embodied_carbon_for_carbon_records(records_res)
    total_carbon_emissions = op_carbon_emissions + emb_carbon_emissions

    summary += "\nCloud Carbon Footprint Method:\n"
    summary += f"- Energy Consumption (exc. PUE): {cpu_energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {cpu_energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {mem_energy}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {mem_energy_pue}kWh\n"
    summary += f"- Operational Carbon Emissions: {op_carbon_emissions}gCO2e\n"
    summary += f"- Embodied Carbon Emissions: {emb_carbon_emissions}gCO2e\n"
    summary += f"- Total Carbon Emissions: {total_carbon_emissions}gCO2e\n"

    print(f"Operational Carbon Emissions: {op_carbon_emissions}gCO2e")
    print(f"Embodied Carbon Emissions: {emb_carbon_emissions}gCO2e")
    print(f"Total Carbon Emissions: {total_carbon_emissions}gCO2e")
    

    if check_reserved_memory_flag:
        total_res_mem_energy: float = 0.0
        total_res_mem_emissions: float = 0.0

        for realtime, ci_val in node_memory_usage:
            res_mem_energy: float = (arguments[RESERVED_MEMORY] * memory_coefficient * realtime * 0.001) * arguments[NUM_OF_NODES]  # convert from W to kW
            total_res_mem_energy += res_mem_energy
            total_res_mem_emissions += res_mem_energy * ci_val

        total_energy: float = total_res_mem_energy + cpu_energy + mem_energy
        res_report: str = f"Reserved Memory Energy Consumption: {total_res_mem_energy}kWh"
        res_ems_report: str = f"Reserved Memory Carbon Emissions: {total_res_mem_emissions}gCO2e"
        energy_split_report: str = f"% CPU [{((cpu_energy / total_energy) * 100):.2f}%] | % Memory [{(((total_res_mem_energy + mem_energy) / total_energy) * 100):.2f}%]"
        summary += f"\n{res_report}\n"
        summary += f"{res_ems_report}\n"
        summary += f"{energy_split_report}\n"
        print(res_report)
        print(energy_split_report)

    if TASK_FLAG:
        total_time: float = 0.0

        for _, tasks_list in tasks_by_interval.items():
            for task in tasks_list:
                total_time += task.realtime

        summary += f"\nTask Runtime: {total_time}ms\n"

    # Report Summary
    if isinstance(ci, float):
        ci = str(int(ci))
    else:
        ci = arguments[CI]

    write_summary_file("output", workflow + "-" + ci + "-" + model_name, summary)
    write_task_trace_and_rank_report("output", workflow + "-" + ci + "-" + model_name, records_res)

    return (summary, total_carbon_emissions)


def get_carbon_footprint(command: str) -> Tuple[str, float]:
    """
    Parse the command and compute the carbon footprint.
    
    :param command: Command string.
    :return: A tuple of (summary string, carbon emissions).
    """
    arguments: Dict[str, Any] = parse_arguments(command.split(' '))
    return main(arguments)


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    args: List[str] = sys.argv[1:]
    arguments: Dict[str, Any] = parse_arguments(args)
    main(arguments)
