"""Module for calculating carbon footprints and exploring temporal shifting of workflows.

This module provides functions to compute energy consumption from tasks, 
apply temporal shifting based on carbon intensity, and generate corresponding reports.
"""

from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord
from src.WorkflowNameConstants import *
from src.Constants import CI, TRACE, PUE, MODEL_NAME, MEMORY_COEFFICIENT, INTERVAL
from src.utils.TimeUtils import to_timestamp, get_intervals, extract_tasks_by_interval
from src.scripts.OperationalCarbon import calculate_carbon_footprint_ccf
from src.utils.Parsers import parse_ci_intervals
from src.utils.Parsers import parse_arguments_TemporalInterrupt

import sys
import numpy as np
from typing import Dict, List, Tuple, Callable, Any


def explore_temporal_shifting_for_workflow(workflow: Any, tasks_by_interval: Dict[str, List[CarbonRecord]], ci: Dict[str, float], model_name: str, overhead_intervals: Dict[int, float], pue: float, memory_coefficient: float, wf_start: int, wf_end: int) -> str:
    """
    Explore shifting of workflow execution times based on minimum carbon intensity.

    Parameters:
        workflow (Any): The workflow identifier.
        tasks_by_hour (Dict[str, List[CarbonRecord]]): Tasks grouped by hour.
        ci (Dict[str, float]): Carbon intensity values keyed by time.
        model_name (str): Model name for utilised resources.
        overhead_intervals (Dict[int, float]): Overhead intervals for shifting.
        pue (float): Power usage effectiveness multiplier.
        memory_coefficient (float): Coefficient for memory consumption.
        wf_start (int): Workflow earliest task timestamp.
        wf_end (int): Workflow latest task completion timestamp. 

    Returns:
        str: A comma-separated string output with original and shifted carbon footprint details.
    """
    # Identify Hours in Order
    intervals_by_key = {}

    for interval, tasks in tasks_by_interval.items():
        if len(tasks) > 0:
            hour_ts = to_timestamp(interval)
            month = str(hour_ts.month).zfill(2)
            day = str(hour_ts.day).zfill(2)
            hh = str(hour_ts.hour).zfill(2)
            mm = str(hour_ts.minute).zfill(2)
            key = f'{month}/{day}-{hh}:{mm}'
            intervals_by_key[key] = tasks

    # Calculate Original Carbon Footprint
    ((_, _, _, _, orig_carbon_emissions, _), _) = calculate_carbon_footprint_ccf(tasks_by_interval, ci, pue, model_name, memory_coefficient, False)

    # Calculate Original Workflow Makespan in seconds
    makespan = (wf_end - wf_start) / 1000

    # Prepare Script Output
    output = [workflow, str(orig_carbon_emissions), str(makespan)]

    # SHIFTING LOGIC
    for shift in [6, 12, 24, 48, 96]:  # flexibility to run over windows 'shift' hours before and after the workflow executed
        keys = list(intervals_by_key.keys())  # keys that the workflow executes over
        wf_intervals = len(keys)  # hours of workflow execution
        ci_keys = list(ci.keys())  # all windows that have ci values, as keys
        start = keys[0]  # workflow start key
        end = keys[-1]  # workflow end key
        start_i = ci_keys.index(start)  # workflow start index
        end_i = ci_keys.index(end)  # workflow end index
        shift_keys = ci_keys[start_i - shift:end_i + shift + 1]  # all keys within the shift
        # reliant on ci data provided being long enough for the shift window, if not this will error

        dat = np.array([ci[key] for key in shift_keys])  # store corresponding ci values for the potential shifts
        ind = sorted(np.argpartition(dat, wf_intervals)[:wf_intervals])  # indices of the minimum ci values
        # the indices are sorted to retain chronological order over time
        min_keys = [shift_keys[i] for i in ind]  # matching keys for the minimum ci values

        ci_for_shifted_trace = {}
        for i in range(0, len(min_keys)):
            ci_for_shifted_trace[keys[i]] = ci[min_keys[i]]

        # Report Optimal CI Temporal Shifting Carbon Footprint
        ((_, _, _, _, carbon_emissions, _), _) = calculate_carbon_footprint_ccf(tasks_by_interval, ci_for_shifted_trace, pue, model_name, memory_coefficient, False)

        # Report Overhead of Interrupting Temporal Shifting
        oh_interval_inds = get_intervals(ind)
        overhead = 0

        if len(overhead_intervals) > 0:
            for oh_interval_ind in oh_interval_inds:
                overhead += overhead_intervals[oh_interval_ind]

        saving = ((orig_carbon_emissions - carbon_emissions) / orig_carbon_emissions) * 100

        overhead_s = overhead / 1000
        overhead_perc = (overhead_s / makespan) * 100

        output.append(f'{saving:.1f}%:{carbon_emissions}:{overhead_s}|{overhead_perc:.1f}%')  # reports overhead in seconds

    return ','.join(output)


def main(workflows: List[Any], ci: Dict[str, float], arguments: Dict[str, Any]) -> None:
    """
    Main function to process workflows and write the temporal shifting report.

    Parameters:
        workflows (List[Any]): List of workflow identifiers.
        ci (Dict[str, float]): Carbon intensity values.
        arguments (Dict[str, Any]): Argument dictionary parsed from command line.

    Returns:
        None
    """
    # Data
    pue: float = arguments[PUE]
    interval: int = arguments[INTERVAL]
    model_name: str = arguments[MODEL_NAME]
    memory_coefficient: float = arguments[MEMORY_COEFFICIENT]
    results = []

    for workflow in workflows:
        ((tasks_by_interval, overhead_intervals), (wf_start, wf_end)) = extract_tasks_by_interval(workflow, interval)

        result = explore_temporal_shifting_for_workflow(workflow, tasks_by_interval, ci, model_name, overhead_intervals, pue, memory_coefficient, wf_start, wf_end)
        results.append(result)

    with open('output/workflows-temp-shift-interrupt.csv', 'w') as f:
        f.write('workflow,footprint,makespan,flexible-6h,flexible-12h,flexible-24h,flexible-48h,flexible-96h\n')

        for result in results:
            f.write(f'{result}\n')


# Main Script
if __name__ == '__main__':
    arguments = sys.argv[1:]
    settings = parse_arguments_TemporalInterrupt(arguments)

    ci_source_file = f"data/intensity/{settings[CI]}.csv"
    ci = parse_ci_intervals(ci_source_file)

    main(WORKFLOWS_TEST, ci, settings)
