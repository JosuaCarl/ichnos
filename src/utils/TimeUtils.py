"""
Module: TimeUtils
This module provides functions for time conversion and manipulation used in the 
carbon footprint calculations. It includes utilities to convert timestamps and 
extract tasks over specified time intervals.
"""

import datetime as time
import copy
import logging
from typing import List

from src.models.TaskExtractionResult import TaskExtractionResult
from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord
from src.models.TasksByTimeResult import TasksByTimeResult
from src.utils.Parsers import parse_trace_file
from src.Constants import FILE, DAY, MONTH, YEAR, HOUR, MINS
from datetime import datetime

# TODO: timezone conversion for non-utc times
def to_timestamp(ms: float) -> time.datetime:
    """
    Convert a millisecond timestamp to a datetime object in UTC.

    :param ms: Milliseconds since epoch.
    :return: datetime object in UTC.
    """
    return time.datetime.fromtimestamp(float(ms) / 1000.0, tz=time.timezone.utc)

def to_timestamp_from_dict(ts_dict: dict) -> datetime:
    """
    Convert a dictionary with time components to a datetime object.
    Expected keys: 'year', 'month', 'day'. 
    Optional keys: 'hour', 'minute', 'second' (default to 0 if missing).
    """
    stamp = datetime.strptime(
        f"{ts_dict[DAY]}/{ts_dict[MONTH]}/{ts_dict[YEAR]} {ts_dict[HOUR]}:{ts_dict[MINS]}", 
        "%d/%m/%Y %H:%M")
    return stamp.timestamp() * 1000

def to_timestamp_from_str(ts_str: str) -> datetime:
    """
    Convert a string timestamp to a datetime object.
    Tries ISO format (e.g. "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS").
    """
    stamp = datetime.strptime(ts_str, "%Y-%m-%dT%H:%MZ")
    return stamp.timestamp() * 1000

def get_tasks_by_hour_with_overhead(start_hour: int, end_hour: int, tasks: List[CarbonRecord]) -> TasksByTimeResult:
    """
    Group tasks by hour with additional overhead calculations.

    :param start_hour: Start time in ms representing the beginning hour.
    :param end_hour: End time in ms representing the ending hour.
    :param tasks: List of task objects.
    :return: A TasksByTimeResult object containing tasks grouped by hour and overheads.
    """
    tasks_by_hour = {}
    overheads = []
    runtimes = []

    step = 60 * 60 * 1000  # 60 minutes in ms
    i = start_hour - step  # start an hour before to be safe

    while i <= end_hour:
        data = []
        hour_overhead = 0

        for task in tasks:
            start = int(task.start)
            complete = int(task.complete)
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            elif complete > i and complete < i + step and start < i:
                partial_task = copy.deepcopy(task)
                partial_task.start = i
                partial_task.realtime = complete - i
                data.append(partial_task)
                runtimes.append(complete - i)
            elif start > i and start < i + step and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.complete = i + step
                partial_task.realtime = i + step - start
                data.append(partial_task)
                if (i + step - start) > hour_overhead:
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
            elif start < i and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.start = i
                partial_task.complete = i + step
                partial_task.realtime = step
                data.append(partial_task)
                runtimes.append(step)

        tasks_by_hour[i] = data
        overheads.append(hour_overhead)
        i += step

    return TasksByTimeResult(tasks_by_time=tasks_by_hour, overheads=overheads)

def get_tasks_by_interval_with_overhead(start_interval: int, end_interval: int, tasks: List[CarbonRecord], interval: int) -> TasksByTimeResult:
    """
    Group tasks by a user-defined interval with overhead calculations.

    :param start_interval: Start interval in ms.
    :param end_interval: End interval in ms.
    :param tasks: List of task objects.
    :param interval: Interval in minutes.
    :return: A TasksByTimeResult object containing tasks grouped by interval and overheads.
    """
    tasks_by_hour = {}
    overheads = []
    runtimes = []

    step = interval * 60 * 1000  # interval minutes in ms
    i = start_interval - step
    end_interval = end_interval + step

    while i <= end_interval:
        data = []
        hour_overhead = 0

        for task in tasks:
            start = int(task.start)
            complete = int(task.complete)
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            elif complete > i and complete < i + step and start < i:
                partial_task = copy.deepcopy(task)
                partial_task.start = i
                partial_task.realtime = complete - i
                data.append(partial_task)
                runtimes.append(complete - i)
            elif start > i and start < i + step and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.complete = i + step
                partial_task.realtime = i + step - start
                data.append(partial_task)
                if (i + step - start) > hour_overhead:
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
            elif start < i and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.start = i
                partial_task.complete = i + step
                partial_task.realtime = step
                data.append(partial_task)
                runtimes.append(step)

        tasks_by_hour[i] = data
        overheads.append(hour_overhead)
        i += step

    return TasksByTimeResult(tasks_by_time=tasks_by_hour, overheads=overheads)


def to_closest_interval_ms(original: float, interval: int) -> int:
    """
    Round a given timestamp (in ms) down to the closest interval (in minutes).

    :param original: Original timestamp in ms.
    :param interval: Interval in minutes.
    :return: Timestamp in ms rounded down to the specified interval.
    """
    ts = to_timestamp(original)
    ts = ts.replace(second=0, microsecond=0)
    ts = ts - time.timedelta(minutes=(ts.minute) % interval)
    return int(ts.timestamp() * 1000)


def get_tasks_by_interval(tasks: List[CarbonRecord], interval: int) -> TaskExtractionResult:
    """
    Extract tasks grouped by a specified interval from a list of tasks.

    :param tasks: List of task objects.
    :param interval: Interval in minutes.
    :return: A TaskExtractionResult object containing tasks grouped by interval and all tasks.
    """
    starts = [int(task.start) for task in tasks]
    ends = [int(task.complete) for task in tasks]
    
    earliest = min(starts)
    latest = max(ends)
    earliest_interval = to_closest_interval_ms(earliest, interval)
    latest_interval = to_closest_interval_ms(latest, interval)
    
    tasks_by_time_result = get_tasks_by_interval_with_overhead(earliest_interval, latest_interval, tasks, interval)
    tasks_by_interval = tasks_by_time_result.tasks_by_time
    
    return TaskExtractionResult(tasks_by_interval=tasks_by_interval, all_tasks=tasks)

def extract_tasks_by_interval(filename: str, interval: int) -> TaskExtractionResult:
    """
    Extract tasks grouped by a specified interval from a trace file.
    
    :param filename: Trace file name (without extension).
    :param interval: Interval in minutes.
    :return: A TaskExtractionResult object from the parsed trace file.
    """
    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]
    try:
        records = parse_trace_file(f"data/trace/{filename}.{FILE}")
    except Exception as e:
        logging.error("Failed to parse trace file %s: %s", f"data/trace/{filename}.{FILE}", e)
        raise
    data_records = []
    for record in records:
        try:
            data = record.make_carbon_record()
            data_records.append(data)
        except Exception as e:
            logging.error("Error converting record to carbon record: %s", e)
    return get_tasks_by_interval(data_records, interval)

def get_intervals(arr: List[int]) -> List[int]:
    """
    Identify discontinuities in a list of interval timestamps to detect overhead periods.

    :param arr: List of consecutive hour timestamps.
    :return: List of indices where discontinuities (gaps) occur.
    """
    intervals = []
    prev = arr[0]
    i = 1
    
    while i < len(arr):
        if not (prev + 1 == arr[i]):
            intervals.append(i - 1)
        prev = arr[i]
        i += 1
    
    return intervals