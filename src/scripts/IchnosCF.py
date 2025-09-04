import datetime
import logging
from typing import Dict, List, Any
from src.utils.TimeUtils import extract_tasks_by_interval
from src.utils.Parsers import parse_ci_intervals, parse_arguments_with_config, parse_trace_file
from src.utils.FileWriters import write_summary_file, write_task_trace_and_rank_report
from src.utils.NodeConfigModelReader import get_cpu_model
from src.scripts.OperationalCarbon import calculate_carbon_footprint_ccf
from src.scripts.EmbodiedCarbon import embodied_carbon_for_trace_records
from src.models.IchnosResult import IchnosResult
from src.models.OperationalCarbonResult import OperationalCarbonResult
from src.models.TaskExtractionResult import TaskExtractionResult

from src.Constants import DELIMITER, DEFAULT_MEMORY_POWER_DRAW, WORKFLOW_NAME,\
TRACE_FILE, TRACE_DELIMITER, CI, CI_FILE, CI_DELIMITER,\
NODE_CONFIG_FILE, OUT_FILES, OUT_FOLDER, OUT_FILE_PREFIX,\
PUE, INTERVAL, MODEL_NAME, MEMORY_COEFFICIENT, RESERVED_MEMORY, NUM_OF_NODES

import sys

def main(args: List[str]) -> IchnosResult:
    """
    Main function to compute and report the carbon footprint.
    
    :param arguments: Argument dictionary parsed from command line.
    :return: An IchnosResult object containing the summary and emissions.
    """
    # Get arguments
    arguments: Dict[str, Any] = parse_arguments_with_config(args)

    # Data
    # Check for required entries
    assert WORKFLOW_NAME in arguments and TRACE_FILE in arguments and (CI in arguments or CI_FILE in arguments)

    # Define trace file
    workflow_name: str = arguments[WORKFLOW_NAME]
    trace_file: str = arguments[TRACE_FILE]
    trace_delimiter:str = arguments.get(TRACE_DELIMITER, DELIMITER)

    # Define Carbon intensity
    ci: float|None = arguments.get(CI, None)
    ci_file: str|None = arguments.get(CI_FILE, None)
    ci_delimiter:str = arguments.get(CI_DELIMITER, DELIMITER)
    ci_map: Dict[str, float]|None = parse_ci_intervals(ci_file, ci_delimiter) if ci_file else None

    # Define other calculation parameters
    node_config_file: str = arguments[NODE_CONFIG_FILE]
    pue: float = arguments[PUE]
    interval: int = arguments[INTERVAL]
    model_name: str = arguments[MODEL_NAME]
    memory_coefficient: float = arguments.get(MEMORY_COEFFICIENT, DEFAULT_MEMORY_POWER_DRAW)

    out_files = arguments.get(OUT_FILES, ["summary", "trace"])
    out_folder = arguments.get(OUT_FOLDER, "output")
    out_file_prefix = arguments.get(OUT_FILE_PREFIX, f"{workflow_name}-{model_name}")
    
    ## Get raw TraceRecords for computing embodied carbon
    try:
        trace_records = parse_trace_file(trace_file, trace_delimiter)
    except Exception as e:
        logging.error("Failed to parse trace file %s: %s", trace_file, e)
        raise e
    
    if ci_file:
        task_extraction_result: TaskExtractionResult = extract_tasks_by_interval(trace_file, interval, trace_delimiter)
        tasks_by_interval = task_extraction_result.tasks_by_interval
    else:
        tasks_by_interval = {datetime.datetime.now(): [trace_record.make_carbon_record() for trace_record in trace_records]}


    # Write summary header
    summary: str = f"""Carbon Footprint Trace:
- carbon-intensity: {arguments[CI]}
- power-usage-effectiveness: {pue}
- power model selected: {model_name}
- memory-power-draw: {memory_coefficient}

"""

    # Reserved memory
    check_node_memory: bool = RESERVED_MEMORY in arguments

    # Calculate carbon emissions (operational & embodied) & save results
    op_carbon_result: OperationalCarbonResult = calculate_carbon_footprint_ccf(tasks_by_interval, ci_map if ci_map else ci, pue, model_name, memory_coefficient, check_node_memory, node_config_file)
    result_attributes = ["cpu_energy", "cpu_energy_pue", "memory_energy", "memory_energy_pue", "carbon_emissions", "node_memory_usage", "records"]
    cpu_energy, cpu_energy_pue, mem_energy, mem_energy_pue, op_carbon_emissions, node_memory_usage, records_res = [getattr(op_carbon_result, attribute) for attribute in result_attributes]

    emb_carbon_emissions = embodied_carbon_for_trace_records(trace_records, use_cpu_usage=False, fallback_cpu_model=get_cpu_model(model_name, node_config_file))
    total_carbon_emissions = op_carbon_emissions + emb_carbon_emissions


    summary += f"""Cloud Carbon Footprint Method:
- Energy Consumption (exc. PUE): {cpu_energy}kWh
- Energy Consumption (inc. PUE): {cpu_energy_pue}kWh
- Memory Energy Consumption (exc. PUE): {mem_energy}kWh
- Memory Energy Consumption (inc. PUE): {mem_energy_pue}kWh
- Operational Carbon Emissions: {op_carbon_emissions}gCO2e
- Embodied Carbon Emissions: {emb_carbon_emissions}gCO2e
- Total Carbon Emissions: {total_carbon_emissions}gCO2e

"""

    print(f"Operational Carbon Emissions: {op_carbon_emissions}gCO2e")
    print(f"Embodied Carbon Emissions: {emb_carbon_emissions}gCO2e")
    print(f"Total Carbon Emissions: {total_carbon_emissions}gCO2e")
    
    if check_node_memory:
        total_res_mem_energy: float = 0.0
        total_res_mem_emissions: float = 0.0

        for realtime, ci_val in node_memory_usage:
            res_mem_energy: float = (arguments[RESERVED_MEMORY] * memory_coefficient * realtime * 0.001) * arguments[NUM_OF_NODES]  # convert from W to kW
            total_res_mem_energy += res_mem_energy
            total_res_mem_emissions += res_mem_energy * ci_val

        total_energy: float = total_res_mem_energy + cpu_energy + mem_energy
        res_report: str = f"Reserved Memory Energy Consumption: {total_res_mem_energy}kWh"
        res_ems_report: str = f"Reserved Memory Carbon Emissions: {total_res_mem_emissions}gCO2e"
        energy_split_report: str = f"% CPU [{((cpu_energy / total_energy) * 100):.2f}%] | % Memory [{(((total_res_mem_energy + mem_energy) / total_energy) * 100):.2f}%]"
        summary += "\n".join([res_report, res_ems_report, energy_split_report, ""])
        print(res_report)
        print(energy_split_report)

    # Report results
    if "summary" in out_files:
        write_summary_file(out_folder, out_file_prefix, summary)
    if "trace" in out_files:
        write_task_trace_and_rank_report(out_folder, out_file_prefix, records_res)

    return IchnosResult(
        summary=summary,
        operational_emissions=op_carbon_result.carbon_emissions,
        embodied_emissions=emb_carbon_emissions
    )


def get_carbon_footprint(command: str) -> IchnosResult:
    """
    Parse the command and compute the carbon footprint.
    
    :param command: Command string.
    :return: A tuple of (summary string, carbon emissions).
    """
    return main(command.split(' '))


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    args: List[str] = sys.argv[1:]
    main(args)
