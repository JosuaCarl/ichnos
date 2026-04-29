# Script to Convert Spark Event Log to Standardized Stage-Node Trace CSV Format
# PLUS: print total computation duration, per-stage durations array, and average stage duration.

from src.utils.Usage import print_usage_exit_SparkEventLogToTrace as print_usage_exit
from src.utils.NodeConfigModelReader import get_system_cores

import json
import csv
import sys
from typing import Dict, Tuple, Optional, List

INPUT_FILE_NAME = "input-file-name"
OUTPUT_FILE = "output-file"
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


def parse_spark_event_log_stage_node_level(input_file_name: str, output_path: str) -> None:
    ip_to_hostname = load_hostname_mapping(input_file_name)
    input_path = f"data/spark_event_logs/{input_file_name}"

    # Per (stage_id, hostname)
    stage_stats: Dict[Tuple[int, str], Dict] = {}

    # Global bounds (whole computation)
    global_min_start_ms: Optional[int] = None
    global_max_end_ms: Optional[int] = None

    # NEW: Per-stage bounds across all nodes
    # stage_bounds[stage_id] = {"min_start_ms": int, "max_end_ms": int}
    stage_bounds: Dict[int, Dict[str, int]] = {}

    with open(input_path, 'r') as infile:
        for line in infile:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("Event") != "SparkListenerTaskEnd":
                continue

            task_info = event.get("Task Info", {})
            task_metrics = event.get("Task Metrics", {})

            stage_id = event.get("Stage ID")
            launch_ms = task_info.get("Launch Time")
            finish_ms = task_info.get("Finish Time")

            if stage_id is None or launch_ms is None or finish_ms is None:
                continue

            # Update global bounds
            if global_min_start_ms is None or launch_ms < global_min_start_ms:
                global_min_start_ms = launch_ms
            if global_max_end_ms is None or finish_ms > global_max_end_ms:
                global_max_end_ms = finish_ms

            # NEW: Update per-stage bounds
            sb = stage_bounds.get(stage_id)
            if sb is None:
                stage_bounds[stage_id] = {"min_start_ms": launch_ms, "max_end_ms": finish_ms}
            else:
                if launch_ms < sb["min_start_ms"]:
                    sb["min_start_ms"] = launch_ms
                if finish_ms > sb["max_end_ms"]:
                    sb["max_end_ms"] = finish_ms

            cpu_time_ns = task_metrics.get("Executor CPU Time", 0)
            peak_mem = task_metrics.get("Peak Execution Memory", 0)

            host_raw = task_info.get("Host", "") or ""
            hostname = ip_to_hostname.get(host_raw, host_raw)

            key = (stage_id, hostname)
            stats = stage_stats.get(key)

            if stats is None:
                stage_stats[key] = {
                    "min_start_ms": launch_ms,
                    "max_end_ms": finish_ms,
                    "total_cpu_time_ns": int(cpu_time_ns) if cpu_time_ns is not None else 0,
                    "max_peak_mem": int(peak_mem) if peak_mem is not None else 0,
                }
            else:
                if launch_ms < stats["min_start_ms"]:
                    stats["min_start_ms"] = launch_ms
                if finish_ms > stats["max_end_ms"]:
                    stats["max_end_ms"] = finish_ms
                stats["total_cpu_time_ns"] += int(cpu_time_ns) if cpu_time_ns is not None else 0
                if peak_mem is not None and peak_mem > stats["max_peak_mem"]:
                    stats["max_peak_mem"] = int(peak_mem)

    # Print whole-computation duration
    if global_min_start_ms is None or global_max_end_ms is None:
        print("[SparkEventLogToTrace] No SparkListenerTaskEnd events found; cannot compute total duration.")
    else:
        total_duration_ms = global_max_end_ms - global_min_start_ms
        total_duration_s = total_duration_ms / 1000.0
        print(
            "[SparkEventLogToTrace] Total computation wall-clock duration "
            f"(first stage start -> last stage end): {total_duration_ms} ms ({total_duration_s:.3f} s)"
        )

    # NEW: Build per-stage durations array + average
    stage_durations_ms: List[int] = []
    stage_durations_s: List[float] = []

    for stage_id in sorted(stage_bounds.keys()):
        sb = stage_bounds[stage_id]
        dur_ms = sb["max_end_ms"] - sb["min_start_ms"]
        if dur_ms < 0:
            # shouldn't happen, but don't crash
            continue
        stage_durations_ms.append(dur_ms)
        stage_durations_s.append(dur_ms / 1000.0)

    if stage_durations_ms:
        avg_stage_duration_ms = sum(stage_durations_ms) / len(stage_durations_ms)
        avg_stage_duration_s = avg_stage_duration_ms / 1000.0

        print(f"[SparkEventLogToTrace] Stage durations (s): {stage_durations_s}")
        print(f"[SparkEventLogToTrace] Average stage duration: {avg_stage_duration_ms:.2f} ms ({avg_stage_duration_s:.3f} s)")
        print(f"[SparkEventLogToTrace] Num stages: {len(stage_durations_ms)}")
    else:
        print("[SparkEventLogToTrace] No stages found for stage-duration computation (no valid task timings).")

    # Write stage+node rows as before
    with open(output_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(CSV_HEADERS)

        for (stage_id, hostname) in sorted(stage_stats.keys(), key=lambda k: (k[0], k[1])):
            stats = stage_stats[(stage_id, hostname)]

            start_ms = stats["min_start_ms"]
            end_ms = stats["max_end_ms"]
            total_cpu_time_ns = stats["total_cpu_time_ns"]
            max_peak_mem = stats["max_peak_mem"]

            duration_ms = end_ms - start_ms
            if duration_ms <= 0:
                continue

            cpu_time_ms = total_cpu_time_ns / 1e6
            cpu_cores_usage = cpu_time_ms / duration_ms # cores
            
            # Get the number of cores from the config
            node_total_cores = get_system_cores(hostname)
            # cpu_util_fraction = cpu_cores_usage / node_total_cores if node_total_cores > 0 else 0
            cpu_util_fraction = cpu_cores_usage # To match nextflow trace format which uses 100% to mean fully utilizing 1 core, so 200% means fully utilizing 2 cores, etc.

            avg_cpu_percent = round(cpu_util_fraction * 100, 2)

            safe_hostname = hostname or "unknown"
            trace_id = f"{stage_id}_{safe_hostname}"
            name = f"stage_{stage_id}_on_{safe_hostname}"

            writer.writerow([
                trace_id,
                name,
                start_ms,
                end_ms,
                node_total_cores,                # cpu_count
                avg_cpu_percent,
                "",               # cpu_model
                max_peak_mem,
                hostname,
                "",               # rapl_timeseries
                ""                # cpu_usage_timeseries
            ])

    print(f"[SparkEventLogToTrace] Successfully converted event log to STAGE+NODE-level trace file [{output_path}]")


def validate_arguments(args: list[str]) -> Dict[str, str]:
    if len(args) != 2:
        print_usage_exit()
    return {INPUT_FILE_NAME: args[0], OUTPUT_FILE: args[1]}


def convert_spark_log(input_file_name: str, output_file: str) -> None:
    parse_spark_event_log_stage_node_level(input_file_name, output_file)


if __name__ == "__main__":
    arguments = sys.argv[1:]
    settings = validate_arguments(arguments)
    convert_spark_log(settings[INPUT_FILE_NAME], settings[OUTPUT_FILE])
