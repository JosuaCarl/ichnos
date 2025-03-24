from src.Constants import *
from src.models.TraceRecord import TraceRecord

def parse_arguments(args):
    if len(args) != 4 and len(args) != 6 and len(args) != 8:
        _print_usage_exit()

    arguments = {}
    arguments[TRACE] = args[0]

    if _check_if_float(args[1]):
        arguments[CI] = float(args[1])
    else:
        arguments[CI] = args[1]

    arguments[MIN_WATTS] = float(args[2])
    arguments[MAX_WATTS] = float(args[3])

    if len(args) == 6:
        arguments[PUE] = float(args[4])
        arguments[MEMORY_COEFFICIENT] = float(args[5])
    elif len(args) == 8:
        arguments[PUE] = float(args[4])
        arguments[MEMORY_COEFFICIENT] = float(args[5])
        arguments[RESERVED_MEMORY] = float(args[6])
        arguments[NUM_OF_NODES] = int(args[7])
    else:
        arguments[PUE] = DEFAULT_PUE_VALUE
        arguments[MEMORY_COEFFICIENT] = DEFAULT_MEMORY_POWER_DRAW

    return arguments


def parse_ci_intervals(filename):
    (header, data) = _get_ci_file_data(filename)

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

##################################
# MARK: Private functions
##################################

def _get_ci_file_data(filename):
    with open(filename, 'r') as file:
        raw = file.readlines()
        header = [val.strip() for val in raw[0].split(",")]
        data = raw[1:]

    return (header, data)

def _print_usage_exit():
    usage = "Ichnos: python -m src.scripts.CarbonFootprint <trace-name> <ci-value|ci-file-name> <min-watts> <max-watts> <? pue=1.0> <? memory-coeff=0.392>"
    print(usage)
    exit(-1)
    
def _check_if_float(value):
	return value.replace('.', '').isnumeric()