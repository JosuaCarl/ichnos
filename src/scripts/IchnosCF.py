from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord, HEADERS
import sys
import datetime as time
import copy


# Default Values
DEFAULT = "default"
FILE = "csv"
DELIMITER = ","
TRACE = "trace"
CI = "ci"
PUE = "pue"
INTERVAL = "interval"
CORE_POWER_DRAW = "core-power-draw"
MEMORY_COEFFICIENT = "memory-coefficient"
MIN_WATTS = "min-watts"
MAX_WATTS = "max-watts"
GA = "GA"
CCF = "CCF"
BOTH = "BOTH"
DEFAULT_PUE_VALUE = 1.0  # Disregard PUE if 1.0
DEFAULT_MEMORY_POWER_DRAW = 0.392  # W/GB
RESERVED_MEMORY = "reserved-memory"
NUM_OF_NODES = "num-of-nodes"
TASK_FLAG = True
MODEL_NAME = 'model-name'
node_min_watts = 48.26
node_max_watts = 124.96333333333332
tdp_per_core = 11.875 


# Functions
def baseline_ga(cpu_usage):
    return 11.875 * cpu_usage

def linear_power_model(cpu_usage):
    return node_min_watts + cpu_usage * (node_max_watts - node_min_watts)

def model_gpg_13_ondemand(cpu_usage):
    return ( 2.120111370111352e-05  * (cpu_usage ** 3) ) + ( -0.010314627039627027  * (cpu_usage ** 2) ) + ( 1.583392126392127  * (cpu_usage ** 1) ) + ( 49.00097902097905  )

def model_gpg_13_performance(cpu_usage):
    return ( 2.861564361564371e-05  * (cpu_usage ** 3) ) + ( -0.010774902874902908  * (cpu_usage ** 2) ) + ( 1.5437219632219659  * (cpu_usage ** 1) ) + ( 50.27918414918414  )

def model_gpg_13_powersave(cpu_usage):
    return ( -1.2509712509706113e-06  * (cpu_usage ** 3) ) + ( -0.00435291375291386  * (cpu_usage ** 2) ) + ( 1.0180155400155448  * (cpu_usage ** 1) ) + ( 48.060862470862425  )

def model_gpg_14_ondemand(cpu_usage):
    return ( 2.5435120435119894e-05  * (cpu_usage ** 3) ) + ( -0.01050792540792533  * (cpu_usage ** 2) ) + ( 1.546503108003105  * (cpu_usage ** 1) ) + ( 50.543682983683055  )

def model_gpg_14_performance(cpu_usage):
    return ( 2.976560476560505e-05  * (cpu_usage ** 3) ) + ( -0.01055419580419587  * (cpu_usage ** 2) ) + ( 1.500831131831135  * (cpu_usage ** 1) ) + ( 51.75289044289049  )

def model_gpg_14_powersave(cpu_usage):
    return ( -1.612276612276791e-06  * (cpu_usage ** 3) ) + ( -0.004015695415695406  * (cpu_usage ** 2) ) + ( 0.9829405594405596  * (cpu_usage ** 1) ) + ( 49.289160839160864  )

def model_gpg_15_ondemand(cpu_usage):
    return ( 1.0183890183890104e-05  * (cpu_usage ** 3) ) + ( -0.008689432789432792  * (cpu_usage ** 2) ) + ( 1.625279202279203  * (cpu_usage ** 1) ) + ( 53.970606060606066  )

def model_gpg_15_performance(cpu_usage):
    return ( 1.10839160839165e-05  * (cpu_usage ** 3) ) + ( -0.008064724164724252  * (cpu_usage ** 2) ) + ( 1.5371985236985277  * (cpu_usage ** 1) ) + ( 55.72610722610721  )

def model_gpg_15_powersave(cpu_usage):
    return ( -3.1598031598030393e-06  * (cpu_usage ** 3) ) + ( -0.004507808857808884  * (cpu_usage ** 2) ) + ( 1.161149313649315  * (cpu_usage ** 1) ) + ( 52.835780885780885  )

def model_gpg_16_ondemand(cpu_usage):
    return ( 2.1170681170680637e-05  * (cpu_usage ** 3) ) + ( -0.008939510489510433  * (cpu_usage ** 2) ) + ( 1.3387931882931874  * (cpu_usage ** 1) ) + ( 46.50426573426577  )

def model_gpg_16_performance(cpu_usage):
    return ( 2.2970085470085892e-05  * (cpu_usage ** 3) ) + ( -0.00890654623154631  * (cpu_usage ** 2) ) + ( 1.3093255633255667  * (cpu_usage ** 1) ) + ( 47.258648018648  )

def model_gpg_16_powersave(cpu_usage):
    return ( 3.1112406112409483e-06  * (cpu_usage ** 3) ) + ( -0.00441396658896663  * (cpu_usage ** 2) ) + ( 0.9267213157213164  * (cpu_usage ** 1) ) + ( 45.58177156177157  )

def model_gpg_22_performance(cpu_usage):
    return ( 0.0007414795389795361  * (cpu_usage ** 3) ) + ( -0.13460499222999192  * (cpu_usage ** 2) ) + ( 8.232617586117582  * (cpu_usage ** 1) ) + ( 131.4333566433568  )

def model_gpg_22_powersave(cpu_usage):
    return ( 0.0008557536907536887  * (cpu_usage ** 3) ) + ( -0.15424075369075355  * (cpu_usage ** 2) ) + ( 9.282093240093246  * (cpu_usage ** 1) ) + ( 110.46752913752906  )



# map from argument to power model
def get_power_model(model_name):
    print(f'Model Name Provided: {model_name}')

    models = {
        "linear": linear_power_model, 
        "gpg_13_ondemand": model_gpg_13_ondemand,
        "gpg_13_performance": model_gpg_13_performance,
        "gpg_13_powersave": model_gpg_13_powersave,
        "gpg_14_ondemand": model_gpg_14_ondemand,
        "gpg_14_performance": model_gpg_14_performance,
        "gpg_14_powersave": model_gpg_14_powersave,
        "gpg_15_ondemand": model_gpg_15_ondemand,
        "gpg_15_performance": model_gpg_15_performance,
        "gpg_15_powersave": model_gpg_15_powersave,
        "gpg_16_ondemand": model_gpg_16_ondemand,
        "gpg_16_performance": model_gpg_16_performance,
        "gpg_16_powersave": model_gpg_16_powersave,
        "gpg_22_performance": model_gpg_22_performance,
        "gpg_22_powersave": model_gpg_22_powersave,
        "baseline": baseline_ga
    }

    if model_name not in models:
        return linear_power_model
    else:
        return models[model_name]


def to_timestamp(ms):
    return time.datetime.fromtimestamp(float(ms) / 1000.0, tz=time.timezone.utc)


def get_ci_file_data(filename):
    with open(filename, 'r') as file:
        raw = file.readlines()
        header = [val.strip() for val in raw[0].split(",")]
        data = raw[1:]

    return (header, data)


def parse_ci_intervals(filename):
    (header, data) = get_ci_file_data(filename)

    date_i = header.index("date")
    start_i = header.index("start")
    value_i = header.index("actual")

    ci_map = {}

    for row in data:
        parts = row.split(",")
        date = parts[date_i]
        month_day = '/'.join([val.zfill(2) for val in date.split('-')[-2:]])
        key = month_day + '-' + parts[start_i]
        value = float(parts[value_i])
        ci_map[key] = value

    return ci_map


def parse_trace_file(filepath):
    with open(filepath, 'r') as file:
        lines = [line.rstrip() for line in file]

    header = lines[0]
    records = []

    for line in lines[1:]:
        trace_record = TraceRecord(header, line, DELIMITER)
        records.append(trace_record)

    return records


def print_usage_exit():
    # Ichnos CF Usage: provide trace, ci, power model (defaults to linear range), interval defaults to 60 minutes, pue defaults to 1.0, memory draw defaults to 0.392
    usage = "Ichnos: python -m src.scripts.IchnosCF <trace-name> <ci-value|ci-file-name> <power_model> <? interval=60> <? pue=1.0> <? memory-coeff=0.392>"
    print(usage)
    exit(-1)


def get_carbon_record(record: TraceRecord):
    return record.make_carbon_record()


def get_tasks_by_hour_with_overhead(start_hour, end_hour, tasks, interval):
    tasks_by_hour = {}
    overheads = []
    runtimes = []

    step = interval * 60 * 1000  # interval minutes in ms
    i = start_hour - step  # start an interval before to be safe
    end_hour = end_hour + step  # finish an interval later to be safe

    while i <= end_hour:
        data = [] 
        hour_overhead = 0

        for task in tasks: 
            start = int(task.get_start())
            complete = int(task.get_complete())
            # full task is within this hour
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            # task ends within this hour (but starts in a previous hour)
            elif complete > i and complete < i + step and start < i:
                # add task from start of this hour until end of hour
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_realtime(complete - i)
                data.append(partial_task)
                runtimes.append(complete - i)
            # task starts within this hour (but ends in a later hour) -- OVERHEAD
            elif start > i and start < i + step and complete > i + step: 
                # add task from start to end of this hour
                partial_task = copy.deepcopy(task)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(i + step - start)
                data.append(partial_task)
                if (i + step - start) > hour_overhead:  # get the overhead for the longest task that starts now but ends later
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
            # task starts before hour and ends after this hour
            elif start < i and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(step)
                data.append(partial_task)
                runtimes.append(step)

        tasks_by_hour[i] = data
        overheads.append(hour_overhead)
        i += step

    # task_overall_runtime = sum(runtimes)

    return (tasks_by_hour, overheads)


# round down to the closest interval
def to_closest_interval_ms(original, interval):
    ts = to_timestamp(original)
    ts = ts.replace(second=0, microsecond=0)
    ts = ts - time.timedelta(minutes=(ts.minute) % interval)
    return int(ts.timestamp() * 1000) 


def get_tasks_by_interval(tasks, interval):
    starts = []
    ends = []

    for task in tasks:
        starts.append(int(task.get_start()))
        ends.append(int(task.get_complete()))

    earliest = min(starts)
    latest = max(ends)
    earliest_hh = to_closest_interval_ms(earliest, interval)
    latest_hh = to_closest_interval_ms(latest, interval)

    return get_tasks_by_hour_with_overhead(earliest_hh, latest_hh, tasks, interval)


def extract_tasks_by_interval(filename, interval):
    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]

    records = parse_trace_file(f"data/trace/{filename}.{FILE}")
    data_records = []

    for record in records:
        data = get_carbon_record(record)
        data_records.append(data)

    return get_tasks_by_interval(data_records, interval)


# Estimate Energy Consumption using CCF Methodology
def estimate_task_energy_consumption_ccf(task: CarbonRecord, model, model_name, memory_coefficient):
    # Time (h)
    time = task.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = task.get_core_count()
    # CPU Usage (%)
    cpu_usage = task.get_cpu_usage() / (100.0 * no_cores)
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


def get_hours(arr):
    hours = []
    prev = arr[0]
    i = 1

    while i < len(arr):
        if not (prev + 1 == arr[i]):  # if not consecutive, workflow halts and resumes
            hours.append(i - 1)  # add the overhead for the previous hour which will not finish by this hour
        prev = arr[i]
        i += 1

    return hours


def check_if_float(value):
    return value.replace('.', '').isnumeric()


def parse_arguments(args):
    if len(args) != 3 and len(args) != 4 and len(args) != 6 and len(args) != 8:
        print_usage_exit()

    arguments = {}
    arguments[TRACE] = args[0]

    if check_if_float(args[1]):
        arguments[CI] = float(args[1])
    else:
        arguments[CI] = args[1]

    arguments[MODEL_NAME] = args[2]

    if len(args) == 4:
        arguments[INTERVAL] = int(args[3])
        arguments[PUE] = DEFAULT_PUE_VALUE
        arguments[MEMORY_COEFFICIENT] = DEFAULT_MEMORY_POWER_DRAW
    elif len(args) == 6:
        arguments[INTERVAL] = int(args[3])
        arguments[PUE] = float(args[4])
        arguments[MEMORY_COEFFICIENT] = float(args[5])
    elif len(args) == 8:
        arguments[INTERVAL] = int(args[3])
        arguments[PUE] = float(args[4])
        arguments[MEMORY_COEFFICIENT] = float(args[5])
        arguments[RESERVED_MEMORY] = float(args[6])
        arguments[NUM_OF_NODES] = int(args[7])
    else:
        arguments[INTERVAL] = 60
        arguments[PUE] = DEFAULT_PUE_VALUE
        arguments[MEMORY_COEFFICIENT] = DEFAULT_MEMORY_POWER_DRAW

    return arguments


def write_trace_file(folder, trace_file, records):
    output_file_name = f"{folder}/{trace_file}-trace.csv"

    with open(output_file_name, "w") as file:
        file.write(f"{HEADERS}\n")

        for record in records:
            file.write(f"{record}\n")


def write_summary_file(folder, trace_file, content):
    output_file_name = f"{folder}/{trace_file}-summary.txt"

    with open(output_file_name, "w") as file:
        file.write(content)


def write_task_trace_and_rank_report(folder, trace_file, records):
    output_file_name = f"{folder}/{trace_file}-detailed-summary.txt"
    technical_output_file_name = f"{folder}/{trace_file}-task-ranked.csv"
    whole_tasks = {}

    for record in records:
        curr_id = record.get_id()
        if curr_id in whole_tasks:
            present = whole_tasks[curr_id]
            whole_tasks[curr_id].set_co2e(present.get_co2e() + record.get_co2e())
            whole_tasks[curr_id].set_energy(present.get_energy() + record.get_energy())
            whole_tasks[curr_id].set_avg_ci(f'{present.get_avg_ci()}|{record.get_avg_ci()}')
            whole_tasks[curr_id].set_realtime(present.get_realtime() + record.get_realtime())
        else:
            whole_tasks[curr_id] = record

    records = whole_tasks.values()
    write_trace_file(folder, trace_file, records)

    sorted_records = sorted(records, key=lambda r: (-r.get_co2e(), -r.get_energy(), -r.get_realtime()))
    sorted_records_par = sorted(records, key=lambda r: (-r.get_energy(), -r.get_realtime()))

    with open(output_file_name, "w") as report_file:
        with open(technical_output_file_name, "w") as task_rank_file:
            report_file.write(f'Detailed Report for {trace_file}\n')
            task_rank_file.write(f'{HEADERS}\nBREAK\n')

            report_file.write('\nTop 10 Tasks - ranked by footprint, energy and realtime:\n')
            task_rank_file.write('TOP|FOOTPRINT-ENERGY-REALTIME\n')
            report_file.write(f'\n{HEADERS}\n')
            for record in sorted_records[:10]:
                report_file.write(f"{record}\n")
                task_rank_file.write(f"{record}\n")

            task_rank_file.write('BREAK\n')
            report_file.write('\nTop 10 Tasks - ranked by energy and realtime:\n')
            report_file.write(f'\n{HEADERS}\n')
            task_rank_file.write('TOP|ENERGY-REALTIME\n')
            for record in sorted_records[:10]:
                report_file.write(f"{record}\n")
                task_rank_file.write(f"{record}\n")

            diff = set(sorted_records[:10]).difference(set(sorted_records_par[:10]))

            if len(diff) == 0:
                report_file.write('\nThe top 10 tasks with the largest energy and realtime have the largest footprint.\n')
                task_rank_file.write('BREAK\nSAME\nEND\n')
            else:
                report_file.write('\nThe following tasks have one of the top 10 largest footprints, but not the highest energy or realtime...\n')
                report_file.write(', '.join([str(task) for task in diff]))
                task_rank_file.write('BREAK\nDIFF\nEND\n')


def main(arguments):
    # Data
    workflow = arguments[TRACE]
    pue = arguments[PUE]
    interval = arguments[INTERVAL]
    model_name = arguments[MODEL_NAME]

    memory_coefficient = arguments[MEMORY_COEFFICIENT]
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
