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
def get_power_model(model_name):
    print(f'Model Name Provided: {model_name}')

    with open('node_config_models/gpgnodes.json') as nodes_json_data:
        models = json.load(nodes_json_data)

        model_found = False
        # Get the model data out of the name
        if model_name.startswith('gpg_'):
            model_data = model_name.split('_')
            if len(model_data) != 4:
                print("Unrecognised model name format. Format should be gpg_<node_id>_<governor>_<model_name>.")
                print("E.g. gpg_13_ondemand_minmax | gpg_13_ondemand_linear | gpg_13_ondemand_cubic | gpg_13_performance_minmax")
                print("Exiting...")
                exit(-1)

            node_id = "gpg_" + model_data[1]
            governor = model_data[2]
            model_type = model_data[3]

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
def estimate_task_energy_consumption_ccf(task: CarbonRecord, model, model_name, memory_coefficient):
    # TODO: Revise this default value (this is for GPG Node 13 OnDemand)
    default_system_cores = 32

    # Time (h)
    time = task.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = task.get_core_count()
    # CPU Usage (%)
    cpu_usage = task.get_cpu_usage() / default_system_cores  # nextflow reports as overall utilisation
    # Memory (GB)
    memory = task.get_memory() / 1073741824  # memory reported in bytes  https://www.nextflow.io/docs/latest/metrics.html 
    # Core Energy Consumption (without PUE)
    core_consumption = time * model(cpu_usage) * 0.001  # convert from W to kW
    if (model_name == 'baseline'):
        core_consumption = core_consumption * no_cores
    # Memory Power Consumption (without PUE)
    memory_consumption = memory * memory_coefficient * time * 0.001  # convert from W to kW
    # Overall and Memory Consumption (kWh) (without PUE)
    return (core_consumption, memory_consumption)


# Estimate Carbon Footprint using CCF Methodology
def calculate_carbon_footprint_ccf(tasks_grouped_by_interval, ci, pue: float, model_name, memory_coefficient, check_node_memory=False):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0
    records = []
    node_memory_used = []
    power_model = get_power_model(model_name)

    for group_interval, tasks in tasks_grouped_by_interval.items():
        if len(tasks) > 0:
            if isinstance(ci, float):
                ci_val = ci
            else:
                hour_ts = to_timestamp(group_interval)
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
                (energy, memory) = estimate_task_energy_consumption_ccf(task, power_model, model_name, memory_coefficient)
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
    # TODO: Revise this default value (this is for GPG Node 13 OnDemand)
    default_node_mem_draw = 0.40268229166666664

    # Data
    workflow = arguments[TRACE]
    pue = arguments[PUE]
    interval = arguments[INTERVAL]
    model_name = arguments[MODEL_NAME]
    memory_coefficient = default_node_mem_draw

    if memory_coefficient == None:
        memory_coefficient = DEFAULT_MEMORY_POWER_DRAW

    (tasks_by_interval, _) = extract_tasks_by_interval(workflow, interval)

    for curr_interval, records in tasks_by_interval.items():
        print(f'interval: {to_timestamp(curr_interval)}')
        if len(records) > 0:
            print(f'tasks: {", ".join([record.get_id() for record in records])}')

    summary = ""
    summary += "Carbon Footprint Trace:\n"
    summary += f"- carbon-intensity: {arguments[CI]}\n"
    summary += f"- power-usage-effectiveness: {pue}\n"
    summary += f"- power model selected: {model_name}\n"
    summary += f"- memory-power-draw: {memory_coefficient}\n"

    if isinstance(arguments[CI], float):
        ci = arguments[CI]
    else:
        ci_filename = f"data/intensity/{arguments[CI]}.{FILE}"
        ci = parse_ci_intervals(ci_filename)

    check_reserved_memory_flag = RESERVED_MEMORY in arguments

    (cf, records) = calculate_carbon_footprint_ccf(tasks_by_interval, ci, pue, model_name, memory_coefficient, check_reserved_memory_flag)
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

        for _, tasks in tasks_by_interval.items():
            for task in tasks:
                time += task.get_realtime()

        hours = time
        summary += f"\nTask Runtime: {hours}ms\n"

    # Report Summary
    if isinstance(ci, float):
        ci = str(int(ci))
    else:
        ci = arguments[CI]

    write_summary_file("output", workflow + "-" + ci + "-" + model_name, summary)
    write_task_trace_and_rank_report("output", workflow + "-" + ci + "-" + model_name, records)

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
