"""
Module: TimeUtils
This module provides functions for time conversion and manipulation used in the 
carbon footprint calculations. It includes utilities to convert timestamps and 
extract tasks over specified time intervals.
"""

import datetime as time
import copy
import logging
from typing import Any, List, Dict, Tuple

from src.models.TraceRecord import TraceRecord
from src.utils.Parsers import parse_trace_file
from src.Constants import FILE

# TODO: timezone conversion for non-utc times

def to_timestamp(ms: float) -> time.datetime:
    """
    Convert a millisecond timestamp to a datetime object in UTC.

    :param ms: Milliseconds since epoch.
    :return: datetime object in UTC.
    """
    return time.datetime.fromtimestamp(float(ms) / 1000.0, tz=time.timezone.utc)

def get_tasks_by_hour_with_overhead(start_hour: int, end_hour: int, tasks: List[Any]) -> Tuple[Dict[int, List[Any]], List[int]]:
    """
    Group tasks by hour with additional overhead calculations.

    :param start_hour: Start time in ms representing the beginning hour.
    :param end_hour: End time in ms representing the ending hour.
    :param tasks: List of task objects.
    :return: Tuple of dictionary mapping hour (ms) to tasks and list of overhead values.
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
            start = int(task.get_start())
            complete = int(task.get_complete())
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            elif complete > i and complete < i + step and start < i:
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_realtime(complete - i)
                data.append(partial_task)
                runtimes.append(complete - i)
            elif start > i and start < i + step and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(i + step - start)
                data.append(partial_task)
                if (i + step - start) > hour_overhead:
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
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

    return (tasks_by_hour, overheads)

def get_tasks_by_interval_with_overhead(start_interval: int, end_interval: int, tasks: List[Any], interval: int) -> Tuple[Dict[int, List[Any]], List[int]]:
    """
    Group tasks by a user-defined interval with overhead calculations.

    :param start_interval: Start interval in ms.
    :param end_interval: End interval in ms.
    :param tasks: List of task objects.
    :param interval: Interval in minutes.
    :return: Tuple of dictionary mapping interval (ms) to tasks and list of overhead values.
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
            start = int(task.get_start())
            complete = int(task.get_complete())
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            elif complete > i and complete < i + step and start < i:
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_realtime(complete - i)
                data.append(partial_task)
                runtimes.append(complete - i)
            elif start > i and start < i + step and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(i + step - start)
                data.append(partial_task)
                if (i + step - start) > hour_overhead:
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
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

    return (tasks_by_hour, overheads)

def to_closest_hour_ms(original: float) -> int:
    """
    Round a given timestamp (in ms) to the closest hour in ms.

    :param original: Original timestamp in ms.
    :return: Timestamp in ms rounded to the closest hour.
    """
    ts = to_timestamp(original)
    if ts.minute >= 30:
        if ts.hour + 1 == 24:
            ts = ts + time.timedelta(days=1)
            ts = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            ts = ts.replace(second=0, microsecond=0, minute=0, hour=ts.hour+1)
    else:
        ts = ts.replace(second=0, microsecond=0, minute=0)
    
    return int(ts.timestamp() * 1000)

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

def get_tasks_by_hour(tasks: List[Any]) -> Tuple[Dict[int, List[Any]], List[int]]:
    """
    Extract tasks grouped by hour from a list of tasks.

    :param tasks: List of task objects.
    :return: Tuple (tasks_by_hour, overheads) as calculated by get_tasks_by_hour_with_overhead.
    """
    starts = []
    ends = []
    
    for task in tasks:
        starts.append(int(task.get_start()))
        ends.append(int(task.get_complete()))
    
    earliest = min(starts)
    latest = max(ends)
    earliest_hh = to_closest_hour_ms(earliest)
    latest_hh = to_closest_hour_ms(latest)
    
    return get_tasks_by_hour_with_overhead(earliest_hh, latest_hh, tasks)

def get_tasks_by_interval(tasks: List[Any], interval: int) -> Tuple[Dict[int, List[Any]], List[int]]:
    """
    Extract tasks grouped by a specified interval from a list of tasks.

    :param tasks: List of task objects.
    :param interval: Interval in minutes.
    :return: Tuple (tasks_by_interval, overheads) as calculated by get_tasks_by_interval_with_overhead.
    """
    starts = []
    ends = []
    
    for task in tasks:
        starts.append(int(task.get_start()))
        ends.append(int(task.get_complete()))
    
    earliest = min(starts)
    latest = max(ends)
    earliest_interval = to_closest_interval_ms(earliest, interval)
    latest_interval = to_closest_interval_ms(latest, interval)
    
    return get_tasks_by_interval_with_overhead(earliest_interval, latest_interval, tasks, interval)

def extract_tasks_by_hour(filename: str) -> Tuple[Dict[int, List[Any]], List[int]]:
    """
    Extract tasks grouped by hour from a trace file.
    
    :param filename: Trace file name (without extension).
    :return: Tuple (tasks_by_hour, overheads) from the parsed trace file.
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
    return get_tasks_by_hour(data_records)

def extract_tasks_by_interval(filename: str, interval: int) -> Tuple[Dict[int, List[Any]], List[int]]:
    """
    Extract tasks grouped by a specified interval from a trace file.
    
    :param filename: Trace file name (without extension).
    :param interval: Interval in minutes.
    :return: Tuple (tasks_by_interval, overheads) from the parsed trace file.
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

def get_hours(arr: List[int]) -> List[int]:
    """
    Identify discontinuities in a list of hourly timestamps to detect overhead periods.

    :param arr: List of consecutive hour timestamps.
    :return: List of indices where discontinuities (gaps) occur.
    """
    hours = []
    prev = arr[0]
    i = 1
    
    while i < len(arr):
        if not (prev + 1 == arr[i]):
            hours.append(i - 1)
        prev = arr[i]
        i += 1
    
    return hours