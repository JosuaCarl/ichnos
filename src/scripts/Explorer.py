# Imports
from src.scripts.Convertor import convertor
from src.scripts.IchnosCF import get_carbon_footprint
from src.utils.Usage import print_usage_exit_Explorer as print_usage_exit

import sys
import os

# Constants
SHIFT_BY_12 = "00-12-00"
SHIFT_BY_6 = "00-06-00"
DEFAULT_SHIFT = SHIFT_BY_12
CMD_SHIFT = "change-time trace delim direction shift filename"
FORWARD = "+"
BACKWARD = "-"
TRACE = "trace"
CI = "ci"
DELIM = "delim"
DIRECTION = "direction"
SHIFT = "shift"
TRACE_FILENAME = "filename"
MODEL_NAME = "model-name"
INTERVAL = "interval"
PUE = "pue"
MEMORY_COEFFICIENT = "memory-coeff"


# Functions
def shift_trace(trace, delim, shift=DEFAULT_SHIFT):
    cmd_shift_forward = CMD_SHIFT\
            .replace(TRACE, trace)\
            .replace(DELIM, delim)\
            .replace(DIRECTION, FORWARD)\
            .replace(SHIFT, shift)\
            .replace(TRACE_FILENAME, f"{trace}~+{shift}")
    cmd_shift_backward = CMD_SHIFT\
            .replace(TRACE, trace)\
            .replace(DELIM, delim)\
            .replace(DIRECTION, BACKWARD)\
            .replace(SHIFT, shift)\
            .replace(TRACE_FILENAME, f"{trace}~-{shift}")

    trace_forward = convertor(cmd_shift_forward)
    trace_backward = convertor(cmd_shift_backward)

    return (trace_backward, trace, trace_forward)


def calculate_footprint(trace, ci, model_name, interval=60, pue=1.0, memory_coeff=0.392):
    command = f"{trace} {ci} {model_name} {interval} {pue} {memory_coeff}"
    return get_carbon_footprint(command)


def report_summary(folder, settings, results):
    file_prefix = folder.split("/")[1]

    with open(folder + f"/{file_prefix}~summary.txt", "w+") as file:
        for (trace, (summary, _)) in results:
            trace_parts = trace.split('.')
            if '~' in trace_parts[0]:
                file.write(f"Trace Report for [{trace_parts[0]}] using CI Data [{settings[CI]}] with Shift [{trace_parts[0].split('~')[1]}]\n")
            else:
                file.write(f"Trace Report for [{trace_parts[0]}] using CI Data [{settings[CI]}] with Shift [0]\n")
            file.write(f"{summary}\n\n")

    with open(folder + f"/{file_prefix}~footprint.csv", "w+") as file:
        file.write('trace,op_ems,emb_ems\n')
        for (trace, (_, (op_cf, emb_cf))) in results:
            file.write(f"{trace.split('.')[0]},{op_cf},{emb_cf}\n")

    print(f"[Explorer] Finished - View Results in [{folder}/summary.txt]")


def get_output_folder(trace, ci): 
    trace_name = trace
    ci_name = ci

    return f"output/explorer-{trace_name}-{ci_name}"


def parse_arguments(arguments):
    if len(arguments) != 7:
        print_usage_exit()

    return {
        TRACE: arguments[0].strip(),
        CI: arguments[1].strip(),
        SHIFT: int(arguments[2].strip()),
        MODEL_NAME: arguments[3].strip(),
        INTERVAL: int(arguments[4].strip()),
        PUE: float(arguments[5].strip()),
        MEMORY_COEFFICIENT: float(arguments[6].strip())
    }


def shift_trace_both_directions_by_h(trace, delim, shift_by, ci, model_name, interval, pue, memory_coeff):
    backward_traces = []
    forward_traces = []

    for i in range(1, shift_by + 1):
        shift = ''

        if i >= 24:
            days = i // 24
            hours = i - (24 * days)
            shift = f"{str(days).zfill(2)}-{str(hours).zfill(2)}-00"
        else:
            shift = f"00-{str(i).zfill(2)}-00"

        (trace_bwd, _, trace_fwd) = shift_trace(trace, delim, shift)
        backward_traces.insert(0, trace_bwd)
        forward_traces.append(trace_fwd)

    footprints = []

    for trace_bwd in backward_traces:
        footprints.append((trace_bwd, calculate_footprint(trace_bwd, ci, model_name, interval, pue, memory_coeff)))

    footprints.append((trace, calculate_footprint(trace, ci, model_name, interval, pue, memory_coeff)))

    for trace_fwd in forward_traces:
        footprints.append((trace_fwd, calculate_footprint(trace_fwd, ci, model_name, interval, pue, memory_coeff)))

    return footprints


# Shift over 2x hour period
if __name__ == "__main__":
    args = sys.argv[1:]
    settings = parse_arguments(args)

    output_folder = get_output_folder(settings[TRACE], settings[CI])
    os.makedirs(output_folder, exist_ok=True)

    footprints = shift_trace_both_directions_by_h(settings[TRACE], ",", settings[SHIFT], settings[CI], settings[MODEL_NAME], settings[INTERVAL], settings[PUE], settings[MEMORY_COEFFICIENT])
    report_summary(output_folder, settings, footprints)
