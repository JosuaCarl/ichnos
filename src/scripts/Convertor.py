from src.utils.Usage import print_usage_exit_Convertor as print_usage_exit

import sys
import re
from datetime import datetime
from typing import Dict, Any, Optional


# Constants
CHANGE_TIME = "change-time"
CHANGE_TIME_MS = "change-time-ms"
CHANGE_START = "change-start"
CHANGE_START_MS = "change-start-ms"
COMMANDS = [CHANGE_TIME, CHANGE_TIME_MS, CHANGE_START, CHANGE_START_MS]
COMMAND = "command"
TRACE_FILE = "trace-file"
DELIMITER = "delimiter"
DIRECTION = "direction"
NEW_START_MS = "new-start-ms"
SHIFT_MS = "shift-ms"
ORIGINAL_START_MS = "original-start-ms"
OUT_FILE = "out-file"

# Functions
def create_trace_file(trace: str, delim: str, offset: int, new_filename: str) -> str:
    """
    Create a new trace file with all start and complete times shifted by a given offset.

    Args:
        trace (str): The base trace filename (without .csv).
        delim (str): The delimiter used in the CSV file.
        offset (int): The offset in milliseconds to shift all times.
        new_filename (str): The output filename for the shifted trace.

    Returns:
        str: The name of the new trace file (without path).
    """
    with open(f'{trace}.csv', 'r') as file:
        raw = file.readlines()
        header = raw[0].split(delim)
        data = raw[1:]

    start_i = header.index("start")
    end_i = header.index("complete")

    with open(new_filename, 'w') as file:
        file.write(delim.join(header))

        for row in data:
            parts = row.split(delim)
            start = int(parts[start_i])
            end = int(parts[end_i])
            new_start = int(start + offset)
            new_end = int(end + offset)
            parts[start_i] = str(new_start)
            parts[end_i] = str(new_end)
            new_row = delim.join(parts)
            file.write(f"{new_row}")

    print(f"[Convertor] Find converted trace file [{new_filename}]")

    return new_filename.split("/")[-1]

def to_timestamp_from_date(time: str) -> float:
    """
    Convert a date string (YYYY-MM-DD:HH-MM) to a timestamp in milliseconds.

    Args:
        time (str): The date string.
    Returns:
        float: The timestamp in milliseconds.
    """
    stamp = datetime.strptime(time, "%Y-%m-%d:%H-%M")
    return stamp.timestamp() * 1000


def to_timestamp_from_dd_hh_mm(time: str) -> int:
    """
    Convert a dd-HH-MM string to a millisecond offset.

    Args:
        time (str): The dd-HH-MM string.
    Returns:
        int: The offset in milliseconds.
    """
    if time[0:2] == '00':
        stamp = datetime.strptime(time[3:], "%H-%M")
        return (stamp.hour * 3600000) + (stamp.minute * 60000)
    else:
        stamp = datetime.strptime(time, "%d-%H-%M")
        return (stamp.day * 86400000) + (stamp.hour * 3600000) + (stamp.minute * 60000)


def validate_arguments(args: list[str]) -> Dict[str, Any]:
    """
    Validate and parse command-line arguments for the Convertor script.

    Args:
        args (list[str]): List of command-line arguments.
    Returns:
        Dict[str, Any]: Parsed and validated settings dictionary.
    """
    if len(args) != 6:
        print_usage_exit()

    if args[0] not in COMMANDS:
        print_usage_exit()

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}:\d{2}-\d{2}$")
    dd_hh_mm_pattern = re.compile(r"^\d{2}-\d{2}-\d{2}$")

    if args[3] != "+" and args[3] != "-":
        if re.match(date_pattern, args[3]) is None and re.match(dd_hh_mm_pattern, args[4]) is None:
            print_usage_exit()
        else:
            new_start = to_timestamp_from_date(args[3])

            if re.match(date_pattern, args[4]) is None:
                original_start = int(args[4])
            else:
                original_start = to_timestamp_from_date(args[4])

            direction = None
            shift_ms = None
    else:
        direction = args[3].strip()
        new_start = None
        original_start = None

        if re.match(dd_hh_mm_pattern, args[4]) is None:
            shift_ms = int(args[4])
        else:
            shift_ms = to_timestamp_from_dd_hh_mm(args[4])  # convert to ms ?

    return {
        COMMAND: args[0],
        TRACE_FILE: f"data/trace/{args[1]}",
        DELIMITER: args[2],
        DIRECTION: direction,
        NEW_START_MS: new_start,
        SHIFT_MS: shift_ms,
        ORIGINAL_START_MS: original_start,
        OUT_FILE: args[5]
    }


def convert(settings: Dict[str, Any]) -> str:
    """
    Perform the trace file conversion based on the provided settings.

    Args:
        settings (Dict[str, Any]): Settings dictionary from argument validation.
    Returns:
        str: The name of the new trace file (without path).
    """
    command = settings[COMMAND]
    filename = settings[TRACE_FILE]
    delimiter = settings[DELIMITER]
    output_filename = f"data/trace/{settings[OUT_FILE]}.csv"
    offset = None

    if command == CHANGE_TIME or command == CHANGE_TIME_MS:
        operator = settings[DIRECTION]
        offset = settings[SHIFT_MS]

        if operator == '-':
            offset *= -1
    elif command == CHANGE_START or command == CHANGE_START_MS: 
        offset = abs(settings[NEW_START_MS] - settings[ORIGINAL_START_MS])

        if settings[NEW_START_MS] < settings[ORIGINAL_START_MS]:
            offset *= -1

    #output_filename += f"~{int(offset)}.{filename[1]}"
    return create_trace_file(filename, delimiter, offset, output_filename)

def convertor(command: str) -> str:
    """
    Entry point for the Convertor script. Parses a command string and performs the conversion.

    Args:
        command (str): The command string to parse and execute.
    Returns:
        str: The name of the new trace file (without path).
    """
    parts = command.split(" ")
    settings = validate_arguments(parts)

    return convert(settings)


# Main
if __name__ == "__main__":
    arguments: list[str] = sys.argv[1:]
    settings = validate_arguments(arguments)

    convert(settings)
