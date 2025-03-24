import os

from src.models.CarbonRecord import HEADERS

def write_trace_file(folder, trace_file, records):
    _create_folder(folder)

    output_file_name = f"{folder}/{trace_file}-trace.csv"

    with open(output_file_name, "w") as file:
        file.write(f"{HEADERS}\n")

        for record in records:
            file.write(f"{record}\n")


def write_summary_file(folder, trace_file, content):
    _create_folder(folder)

    output_file_name = f"{folder}/{trace_file}-summary.txt"

    with open(output_file_name, "w") as file:
        file.write(content)
        

def _create_folder(folder):
		if not os.path.exists(folder):
				os.makedirs(folder)