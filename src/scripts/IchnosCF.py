from src.models.CarbonRecord import CarbonRecord
from src.utils.TimeUtils import to_timestamp, extract_tasks_by_interval
from src.utils.Parsers import parse_ci_intervals, parse_arguments
from src.utils.FileWriters import write_summary_file, write_task_trace_and_rank_report
import src.utils.MathModels as MathModels
from src.Constants import *
import sys

# Node Specific Configuration
# GPG Node 13 - Governor [ondemand]
node_min_watts = 48.26
node_max_watts = 124.96333333333332
tdp_per_core = 11.875
system_cores = 32
node_mem_draw = 0.40268229166666664

# Functions
baseline_ga = MathModels.linear_model(tdp_per_core / 100, 0)
linear_power_model = MathModels.linear_model((node_max_watts - node_min_watts) / 100, node_min_watts)

model_gpg_13_ondemand = MathModels.cubic_model(2.120111370111352e-05, -0.010314627039627027, 1.583392126392127, 49.00097902097905)
model_gpg_13_ondemand_linear = MathModels.linear_model(0.7486757575757578, 60.465909090909086)
model_gpg_14_performance = MathModels.cubic_model(2.976560476560505e-05, -0.01055419580419587, 1.500831131831135, 51.75289044289049)
model_gpg_14_performance_linear = MathModels.linear_model(0.7216363636363639, 61.95848484848483)
model_gpg_14_powersave = MathModels.cubic_model(-1.612276612276791e-06, -0.004015695415695406, 0.9829405594405596, 49.289160839160864)
model_gpg_14_powersave_linear = MathModels.linear_model(0.5664090909090908, 55.61742424242428)
model_gpg_15_performance = MathModels.cubic_model(1.10839160839165e-05, -0.008064724164724252, 1.5371985236985277, 55.72610722610721)
model_gpg_15_performance_linear = MathModels.linear_model(0.8335848484848487, 65.72833333333334)
model_gpg_15_powersave = MathModels.cubic_model(-3.1598031598030393e-06, -0.004507808857808884, 1.161149313649315, 52.835780885780885)
model_gpg_15_powersave_linear = MathModels.linear_model(0.6810454545454548, 60.19469696969696)
model_gpg_16_ondemand = MathModels.cubic_model(2.1170681170680637e-05, -0.008939510489510433, 1.3387931882931874, 46.50426573426577)
model_gpg_16_ondemand_linear = MathModels.linear_model(0.6413060606060605, 55.91227272727273)
model_gpg_22_performance = MathModels.cubic_model(0.0007414795389795361, -0.13460499222999192, 8.232617586117582, 131.4333566433568)
model_gpg_22_performance_linear = MathModels.linear_model(1.6530484848484859, 193.20121212121217)
model_gpg_22_powersave = MathModels.cubic_model(0.0008557536907536887, -0.15424075369075355, 9.282093240093246, 110.46752913752906)
model_gpg_22_powersave_linear = MathModels.linear_model(1.7994121212121201, 180.0912121212122)


# map from argument to power model
def get_power_model(model_name):
    print(f'Model Name Provided: {model_name}')

    models = {
        "linear": linear_power_model, 
        "gpg_13_ondemand": model_gpg_13_ondemand,
        "gpg_13_ondemand_linear": model_gpg_13_ondemand_linear,
        "gpg_14_performance": model_gpg_14_performance,
        "gpg_14_performance_linear": model_gpg_14_performance_linear,
        "gpg_14_powersave": model_gpg_14_powersave,
        "gpg_14_powersave_linear": model_gpg_14_powersave_linear,
        "gpg_15_performance": model_gpg_15_performance,
        "gpg_15_performance_linear": model_gpg_15_performance_linear,
        "gpg_15_powersave": model_gpg_15_powersave,
        "gpg_15_powersave_linear": model_gpg_15_powersave_linear,
        "gpg_16_ondemand": model_gpg_16_ondemand,
        "gpg_16_ondemand_linear": model_gpg_16_ondemand_linear,
        "gpg_22_performance": model_gpg_22_performance,
        "gpg_22_performance_linear": model_gpg_22_performance_linear,
        "gpg_22_powersave": model_gpg_22_powersave,
        "gpg_22_powersave_linear": model_gpg_22_powersave_linear,
        "baseline": baseline_ga
    }

    if model_name not in models:
        return linear_power_model
    else:
        return models[model_name]

# Estimate Energy Consumption
def estimate_task_energy_consumption_ccf(task: CarbonRecord, model, model_name, memory_coefficient):
    # Time (h)
    time = task.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = task.get_core_count()
    # CPU Usage (%)
    cpu_usage = task.get_cpu_usage() / system_cores  # nextflow reports as overall utilisation
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
    # Data
    workflow = arguments[TRACE]
    pue = arguments[PUE]
    interval = arguments[INTERVAL]
    model_name = arguments[MODEL_NAME]
    memory_coefficient = node_mem_draw

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
