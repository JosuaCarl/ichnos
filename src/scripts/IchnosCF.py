from typing import Any, Callable, Dict, List, Tuple, Union
from src.models.CarbonRecord import CarbonRecord
from src.utils.TimeUtils import to_timestamp, extract_tasks_by_interval
from src.utils.Parsers import parse_ci_intervals, parse_arguments
from src.utils.FileWriters import write_summary_file, write_task_trace_and_rank_report
import src.utils.MathModels as MathModels
from src.Constants import *
import json
import sys

"""
Model name format: gpg_<node_id>_<governor>_<model_name>
where governor is either 'ondemand', 'performance', or 'powersave'
and model_name is either 'linear', 'minmax', 'cubic', or 'baseline'"
"""
def get_power_model(model_name: str) -> Any:
    """Return a power model function based on the provided model name."""
    print(f'Model Name Provided: {model_name}')

    with open('node_config_models/gpgnodes.json') as nodes_json_data:
        models = json.load(nodes_json_data)

        model_found: bool = False
        # Get the model data out of the name
        if model_name.startswith('gpg_'):
            model_data = model_name.split('_')
            if len(model_data) != 4:
                print("Unrecognised model name format. Format should be gpg_<node_id>_<governor>_<model_name>.")
                print("E.g. gpg_13_ondemand_minmax | gpg_13_ondemand_linear | gpg_13_ondemand_cubic | gpg_13_performance_minmax")
                print("Exiting...")
                exit(-1)

            node_id: str = "gpg_" + model_data[1]
            governor: str = model_data[2]
            model_type: str = model_data[3]

            # TODO: Refactor this to be more readable
            model_found = node_id in models and governor in models[node_id] and (model_type in models[node_id][governor] or (model_type == 'minmax' and 'min_watts' in models[node_id][governor]) and 'max_watts' in models[node_id][governor])

        if not model_found:
            print("Unrecognised model name. Using default gpg_13_ondemand_minmax model.")
            node_id = "gpg_13"
            governor = "ondemand"
            model_type = "minmax"

        if model_type == 'minmax':
            min_watts = models[node_id][governor]['min_watts']
            max_watts = models[node_id][governor]['max_watts']
            return MathModels.min_max_linear_power_model(min_watts, max_watts)
        elif model_type == 'baseline':
            tdp_per_core = models[node_id][governor]['tdp_per_core']
            return MathModels.baseline_power_model(tdp_per_core)

        return MathModels.polynomial_model(models[node_id][governor][model_type])

# Estimate Energy Consumption
def estimate_task_energy_consumption_ccf(task: CarbonRecord, model: Callable[[float], float], model_name: str, memory_coefficient: float) -> Tuple[float, float]:
    """
    Estimate the energy consumptions for a task.
    
    :param task: CarbonRecord of the task.
    :param model: Power model function.
    :param model_name: Name of the power model.
    :param memory_coefficient: Coefficient for memory power draw.
    :return: Tuple (core energy consumption, memory energy consumption) in kWh.
    """
    # TODO: Revise this default value (this is for GPG Node 13 OnDemand)
    default_system_cores: int = 32

    # Time (h)
    time_h: float = task.realtime / 1000 / 3600  # convert from ms to hours
    # Number of Cores (int)
    no_cores: int = task.core_count
    # CPU Usage (%)
    cpu_usage: float = task.cpu_usage / default_system_cores  # nextflow reports as overall utilisation
    # Memory (GB)
    memory: float = task.memory / 1073741824  # memory reported in bytes  https://www.nextflow.io/docs/latest/metrics.html 
    # Core Energy Consumption (without PUE)
    core_consumption: float = time_h * model(cpu_usage) * 0.001  # convert from W to kW
    if model_name == 'baseline':
        core_consumption *= no_cores
    # Memory Power Consumption (without PUE)
    memory_consumption: float = memory * memory_coefficient * time_h * 0.001  # convert from W to kW
    # Overall and Memory Consumption (kWh) (without PUE)
    return (core_consumption, memory_consumption)


# Estimate Carbon Footprint using CCF Methodology
def calculate_carbon_footprint_ccf(tasks_grouped_by_interval: Dict[Any, List[CarbonRecord]], ci: Union[float, Dict[str, float]], pue: float, model_name: str, memory_coefficient: float, check_node_memory: bool = False) -> Tuple[Tuple[float, float, float, float, float, List[Any]], List[CarbonRecord]]:
    """
    Calculate the carbon footprint using the CCF methodology.
    
    :param tasks_grouped_by_interval: Dict mapping interval to list of tasks.
    :param ci: Carbon intensity as a float or dict.
    :param pue: Power usage effectiveness.
    :param model_name: Power model name.
    :param memory_coefficient: Memory power draw coefficient.
    :param check_node_memory: Flag to check reserved memory.
    :return: Tuple containing aggregated metrics and a list of processed tasks.
    """
    total_energy: float = 0.0
    total_energy_pue: float = 0.0
    total_memory_energy: float = 0.0
    total_memory_energy_pue: float = 0.0
    total_carbon_emissions: float = 0.0
    records: List[CarbonRecord] = []
    node_memory_used: List[Any] = []
    power_model = get_power_model(model_name)

    for group_interval, tasks in tasks_grouped_by_interval.items():
        if tasks:
            if isinstance(ci, float):
                ci_val: float = ci
            else:
                hour_ts = to_timestamp(group_interval)
                hh: str = str(hour_ts.hour).zfill(2)
                month: str = str(hour_ts.month).zfill(2)
                day: str = str(hour_ts.day).zfill(2)
                mm: str = str(hour_ts.minute).zfill(2)
                ci_key: str = f'{month}/{day}-{hh}:{mm}'
                ci_val = ci[ci_key] 

            if check_node_memory:
                starts: List[int] = [int(task.start) for task in tasks]
                ends: List[int] = [int(task.complete) for task in tasks]

                earliest: int = min(starts)
                latest: int = max(ends)
                realtime: float = (latest - earliest) / 1000 / 3600  # convert from ms to h 
                node_memory_used.append((realtime, ci_val))

            for task in tasks:
                energy, memory = estimate_task_energy_consumption_ccf(task, power_model, model_name, memory_coefficient)
                energy_pue: float = energy * pue
                memory_pue: float = memory * pue
                task_footprint: float = (energy_pue + memory_pue) * ci_val
                task.energy = energy_pue
                task.co2e = task_footprint
                task.avg_ci = ci_val
                total_energy += energy
                total_energy_pue += energy_pue
                total_memory_energy += memory
                total_memory_energy_pue += memory_pue
                total_carbon_emissions += task_footprint
                records.append(task)

    return ((total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions, node_memory_used), records)

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
    cpu_energy, cpu_energy_pue, mem_energy, mem_energy_pue, carbon_emissions, node_memory_usage = cf

    summary += "\nCloud Carbon Footprint Method:\n"
    summary += f"- Energy Consumption (exc. PUE): {cpu_energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {cpu_energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {mem_energy}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {mem_energy_pue}kWh\n"
    summary += f"- Carbon Emissions: {carbon_emissions}gCO2e"

    print(f"Carbon Emissions: {carbon_emissions}gCO2e")

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

    return (summary, carbon_emissions)


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
