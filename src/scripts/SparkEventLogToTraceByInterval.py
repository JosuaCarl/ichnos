#!/usr/bin/env python3
# Convert Spark Event Log -> Standardized TRACE CSV
# Grouping granularity: FIXED TIME INTERVALS (passed as CLI argument), split by NODE.
#
# Also prints:
#  - total computation wall-clock duration (earliest task launch -> latest task finish)
#  - the duration of each interval bucket (array) and the average bucket duration
#
# Usage:
#   python3 SparkEventLogToTrace.py <input_eventlog_filename> <output_csv_path> <interval_seconds>
#
# Example:
#   python3 SparkEventLogToTrace.py app_123_eventlog.json out.csv 1
#   python3 SparkEventLogToTrace.py app_123_eventlog.json out.csv 0.2

from src.utils.Usage import print_usage_exit_SparkEventLogToTrace as print_usage_exit
from src.utils.NodeConfigModelReader import get_system_cores

import json
import csv
import sys
import math
from typing import Dict, Tuple, Optional, List, Any


INPUT_FILE_NAME = "input-file-name"
OUTPUT_FILE = "output-file"
INTERVAL_SECONDS = "interval-seconds"

CSV_HEADERS = [
    "id", "name", "start", "end", "cpu_count", "avg_cpu_usage",
    "cpu_model", "memory", "hostname", "rapl_timeseries", "cpu_usage_timeseries"
]


def load_hostname_mapping(input_file_name: str) -> Dict[str, str]:
    base_name = input_file_name.rsplit('.', 1)[0] if '.' in input_file_name else input_file_name
    mapping_file_path = f"data/spark_event_logs/{base_name}_hosts.csv"

    ip_to_hostname: Dict[str, str] = {}

    try:
        with open(mapping_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ip = row.get('ip', '').strip()
                hostname = row.get('hostname', '').strip()
                if ip and hostname:
                    ip_to_hostname[ip] = hostname
        print(f"[SparkEventLogToTrace] Loaded {len(ip_to_hostname)} hostname mappings from [{mapping_file_path}]")
    except FileNotFoundError:
        print(f"[SparkEventLogToTrace] No hostname mapping file found at [{mapping_file_path}], using IP addresses")
    except Exception as e:
        print(f"[SparkEventLogToTrace] Error reading hostname mapping: {e}, using IP addresses")

    return ip_to_hostname


def parse_float_interval_seconds(s: str) -> float:
    try:
        v = float(s)
    except ValueError:
        raise ValueError(f"interval_seconds must be numeric, got {s!r}")
    if v <= 0:
        raise ValueError(f"interval_seconds must be > 0, got {v}")
    return v


def parse_spark_event_log_interval_node_level(
    input_file_name: str,
    output_path: str,
    interval_seconds: float,
) -> None:
    """
    Group tasks into fixed-size time windows (interval_seconds), split by hostname.

    Window alignment: relative to the earliest task launch time in the log
    (i.e., bucket 0 starts at global_min_start_ms).
    """
    ip_to_hostname = load_hostname_mapping(input_file_name)
    input_path = f"data/spark_event_logs/{input_file_name}"
    interval_ms = int(round(interval_seconds * 1000.0))
    if interval_ms <= 0:
        # If user gave a tiny float that rounds to 0ms, clamp to 1ms
        interval_ms = 1

    # First pass: collect all task records we need + global bounds.
    global_min_start_ms: Optional[int] = None
    global_max_end_ms: Optional[int] = None

    # Keep task records so we can bucket them after we know global_min_start_ms.
    # record = (hostname, launch_ms, finish_ms, cpu_time_ns, peak_mem)
    task_records: List[Tuple[str, int, int, int, int]] = []

    with open(input_path, 'r') as infile:
        for line in infile:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("Event") != "SparkListenerTaskEnd":
                continue

            task_info = event.get("Task Info", {}) or {}
            task_metrics = event.get("Task Metrics", {}) or {}

            launch_ms = task_info.get("Launch Time")
            finish_ms = task_info.get("Finish Time")
            if launch_ms is None or finish_ms is None:
                continue

            if global_min_start_ms is None or launch_ms < global_min_start_ms:
                global_min_start_ms = launch_ms
            if global_max_end_ms is None or finish_ms > global_max_end_ms:
                global_max_end_ms = finish_ms

            host_raw = task_info.get("Host", "") or ""
            hostname = ip_to_hostname.get(host_raw, host_raw)

            cpu_time_ns = task_metrics.get("Executor CPU Time", 0) or 0
            peak_mem = task_metrics.get("Peak Execution Memory", 0) or 0

            task_records.append((
                hostname,
                int(launch_ms),
                int(finish_ms),
                int(cpu_time_ns),
                int(peak_mem),
            ))

    if global_min_start_ms is None or global_max_end_ms is None or not task_records:
        print("[SparkEventLogToTrace] No SparkListenerTaskEnd events found; nothing to convert.")
        # Still write an empty CSV with headers for consistency
        with open(output_path, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(CSV_HEADERS)
        return

    # Decide number of windows that cover [global_min_start_ms, global_max_end_ms]
    # We make windows half-open: [start, end), except last for printing it doesn't matter.
    # num_windows >= 1
    num_windows = max(1, int(math.ceil((global_max_end_ms - global_min_start_ms) / interval_ms)))
    # If end == start, ceil(0)=0 => clamp to 1
    if num_windows == 0:
        num_windows = 1


    # Aggregate by (hostname, window_index)
    # bucket_stats[(hostname, w)] = {
    #   "total_cpu_time_ns": int,
    #   "max_peak_mem": int,
    #   "min_task_start_ms": int,
    #   "max_task_end_ms": int
    # }
    bucket_stats: Dict[Tuple[str, int], Dict[str, Any]] = {}

    for (hostname, launch_ms, finish_ms, cpu_time_ns, peak_mem) in task_records:
        # Assign task to a window based on its LAUNCH time relative to global start.
        # (Alternative is midpoint, or splitting across windows, but launch-time assignment is simplest.)
        w = int((launch_ms - global_min_start_ms) // interval_ms)
        # Clamp in case of weird negatives
        if w < 0:
            w = 0
        if w >= num_windows:
            w = num_windows - 1

        key = (hostname, w)
        stats = bucket_stats.get(key)
        if stats is None:
            bucket_stats[key] = {
                "total_cpu_time_ns": cpu_time_ns,
                "max_peak_mem": peak_mem,
                "min_task_start_ms": launch_ms,
                "max_task_end_ms": finish_ms,
            }
        else:
            stats["total_cpu_time_ns"] += cpu_time_ns
            if peak_mem > stats["max_peak_mem"]:
                stats["max_peak_mem"] = peak_mem
            if launch_ms < stats["min_task_start_ms"]:
                stats["min_task_start_ms"] = launch_ms
            if finish_ms > stats["max_task_end_ms"]:
                stats["max_task_end_ms"] = finish_ms

    # Emit one row per (hostname, window_index) that actually had tasks
    with open(output_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(CSV_HEADERS)

        # Sort deterministically by window then hostname
        for (hostname, w) in sorted(bucket_stats.keys(), key=lambda k: (k[1], k[0])):
            stats = bucket_stats[(hostname, w)]
            total_cpu_time_ns = stats["total_cpu_time_ns"]
            max_peak_mem = stats["max_peak_mem"]

            window_start_ms = global_min_start_ms + w * interval_ms
            window_end_ms = window_start_ms + interval_ms
            window_duration_ms = window_end_ms - window_start_ms
            if window_duration_ms <= 0:
                continue

            # Convert total CPU time -> average core usage in the window
            cpu_time_ms = total_cpu_time_ns / 1e6
            cpu_cores_usage = cpu_time_ms / window_duration_ms  # "core-seconds per second" in this window (i.e., cores)

            node_total_cores = get_system_cores(hostname)
            cpu_util_fraction = (cpu_cores_usage / node_total_cores) if node_total_cores > 0 else 0.0
            avg_cpu_percent = round(cpu_util_fraction * 100, 2)

            safe_hostname = hostname or "unknown"
            trace_id = f"win{w}_{safe_hostname}"
            name = f"window_{w}_on_{safe_hostname}"

            writer.writerow([
                trace_id,
                name,
                window_start_ms,
                window_end_ms,
                node_total_cores if node_total_cores > 0 else 1,  # cpu_count now reflects node core count
                avg_cpu_percent,
                "",                   # cpu_model
                max_peak_mem,
                hostname,
                "",                   # rapl_timeseries
                ""                    # cpu_usage_timeseries
            ])

    print(f"[SparkEventLogToTrace] Successfully converted event log to INTERVAL+NODE trace file [{output_path}]")


def validate_arguments(args: list[str]) -> Dict[str, str]:
    # Expect: input, output, interval_seconds
    if len(args) != 3:
        print_usage_exit()

    interval_seconds = parse_float_interval_seconds(args[2])

    return {
        INPUT_FILE_NAME: args[0],
        OUTPUT_FILE: args[1],
        INTERVAL_SECONDS: str(interval_seconds),
    }


def convert_spark_log(input_file_name: str, output_file: str, interval_seconds: float) -> None:
    parse_spark_event_log_interval_node_level(input_file_name, output_file, interval_seconds)


if __name__ == "__main__":
    arguments = sys.argv[1:]
    settings = validate_arguments(arguments)
    convert_spark_log(
        settings[INPUT_FILE_NAME],
        settings[OUTPUT_FILE],
        float(settings[INTERVAL_SECONDS]),
    )
