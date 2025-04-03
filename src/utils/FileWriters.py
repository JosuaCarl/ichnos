"""
Module: FileWriters
This module contains functions to write output files such as summary reports, 
detailed trace reports, and any other file-based outputs required by the project.
"""

import os
import logging
from typing import Iterable, Any
from src.models.CarbonRecord import HEADERS

def write_trace_file(folder: str, trace_file: str, records: Iterable[Any]) -> None:
    """
    Write trace records to a CSV file.
    
    :param folder: Directory where the file will be saved.
    :param trace_file: Base name for the trace file.
    :param records: Iterable of trace record objects.
    """
    _create_folder(folder)
    output_file_name = f"{folder}/{trace_file}-trace.csv"
    try:
        with open(output_file_name, "w") as file:
            file.write(f"{HEADERS}\n")
            for record in records:
                file.write(f"{record}\n")
    except Exception as e:
        logging.error("Failed to write trace file %s: %s", output_file_name, e)
        raise

def write_summary_file(folder: str, trace_file: str, content: str) -> None:
    """
    Write a summary report to a text file.
    
    :param folder: Directory where the file will be saved.
    :param trace_file: Base name for the summary file.
    :param content: Text content of the summary.
    """
    _create_folder(folder)
    output_file_name = f"{folder}/{trace_file}-summary.txt"
    try:
        with open(output_file_name, "w") as file:
            file.write(content)
    except Exception as e:
        logging.error("Failed to write summary file %s: %s", output_file_name, e)
        raise

def write_trace_and_detailed_report(folder: str, trace_file: str, records: Iterable[Any], content: str) -> None:
    """
    Write both detailed trace and summary reports.
    
    :param folder: Directory where files will be saved.
    :param trace_file: Base name to use for output files.
    :param records: Iterable of trace record objects.
    :param content: Summary content to include in the detailed report.
    """
    output_file_name = f"{folder}/{trace_file}-detailed-summary.txt"
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
    try:
        write_trace_file(folder, trace_file, records)
    except Exception as e:
        logging.error("Error writing trace file from detailed report: %s", e)
        raise
    sorted_records = sorted(records, key=lambda r: (-r.get_co2e(), -r.get_energy(), -r.get_realtime()))
    sorted_records_par = sorted(records, key=lambda r: (-r.get_energy(), -r.get_realtime()))
    try:
        with open(output_file_name, "w") as file:
            file.write(f'Detailed Report for {trace_file}\n')
            file.write('\nTop 10 Tasks - ranked by footprint, energy and realtime:\n')
            for record in sorted_records[:10]:
                file.write(record.get_name() + ':' + record.get_id() + '\n')
            file.write('\nTop 10 Tasks - ranked by energy and realtime:\n')
            for record in sorted_records_par[:10]:
                file.write(record.get_name() + ':' + record.get_id() + '\n')
            diff = set(sorted_records[:10]).difference(set(sorted_records_par[:10]))
            if len(diff) == 0:
                file.write('\nThe top 10 tasks with the largest energy and realtime have the largest footprint.\n')
            else:
                file.write('\nThe following tasks have one of the top 10 largest footprints, but not the highest energy or realtime...\n')
                file.write(', '.join([record.get_name() + ':' + record.get_id() for record in diff]))
    except Exception as e:
        logging.error("Failed to write detailed report file %s: %s", output_file_name, e)
        raise

def write_task_trace_and_rank_report(folder: str, trace_file: str, records: Iterable[Any]) -> None:
    """
    Write detailed and ranked task reports.
    
    :param folder: Directory where files will be saved.
    :param trace_file: Base name for the output files.
    :param records: Iterable of trace record objects.
    """
    _create_folder(folder)
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
    try:
        write_trace_file(folder, trace_file, records)
    except Exception as e:
        logging.error("Error writing trace file for task rank report: %s", e)
        raise
    sorted_records = sorted(records, key=lambda r: (-r.get_co2e(), -r.get_energy(), -r.get_realtime()))
    sorted_records_par = sorted(records, key=lambda r: (-r.get_energy(), -r.get_realtime()))
    try:
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
    except Exception as e:
        logging.error("Failed to write task trace and rank report files: %s", e)
        raise

##################################
# MARK: Private Functions
##################################
def _create_folder(folder: str) -> None:
    """
    Create the folder if it does not already exist.
    
    :param folder: Directory path to create.
    """
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
    except Exception as e:
        logging.error("Failed to create folder %s: %s", folder, e)
        raise