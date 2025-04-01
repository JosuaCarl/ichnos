from src.Constants import ELECTRICITY_MAPS, NATIONAL_GRID

def print_usage_exit_TemporalInterrupt():
    usage = "$ python -m src.scripts.TemporalInterrupt <ci-file-name> <pue> <memory_coefficient> <min-watts> <max-watts>"
    example = "$ python -m src.scripts.TemporalInterrupt ci 1.0 0.392 65 219"

    print(usage)
    print(example)
    exit(-1)

def print_usage_exit_FetchCarbonIntensity():
    print("[FetchCarbonIntensity] Usage: py FetchCarbonIntensity.py <source> <YYYY-MM-DD:HH-MM> <YYYY-MM-DD:HH-MM>")
    print(f"[FetchCarbonIntensity] $ py FetchCarbonIntensity.py {ELECTRICITY_MAPS} 2024-03-01:09-00 2024-03-03:17-00")
    print(f"[FetchCarbonIntensity] $ py FetchCarbonIntensity.py {NATIONAL_GRID} 2024-03-01:09-00 2024-03-01:17-00")
    exit(-1)
    
def print_usage_exit_ExtractTimeline():
    usage = "carbon-footprint $ python -m src.scripts.ExtractTimeline <trace-file-name>"
    example = "carbon-footprint $ python -m src.scripts.ExtractTimeline test"

    print(usage)
    print(example)
    exit(-1)
    
def print_usage_exit_ExportCarbonIntensity():
    usage = "[ExportCarbonIntensity] Expected Usage: py ExportCarbonIntensity.py <YYYY-MM-DD> <YYYY-MM-DD> <region>"
    example = "[ExportCarbonIntensity] Example Use: py ExportCarbonIntensity.py 2023-11-26 2023-11-28 de"
    print(usage)
    print(example)
    exit(-1)
    
def print_usage_exit_Explorer():
    usage = "[Explorer] Expected Usage: py explorer.py <trace-file> <ci-file> <config> <shift> <min-watts> <max-watts>"
    example = "[Explorer] Example Use: py explorer.py test.csv ci-20240218.csv default 12 30 80"
    print(usage)
    print(example)
    exit(-1)
    
def print_usage_exit_Convertor():
    usage = "[Convertor] $ Expected Use - Arguments Format: <change-command> <trace-file-name.end> <delimiter> <direction|new-start> <shift|original-start> <output-name>"
    example_time = "[Convertor] $ adjust file by days-hours-minutes: change-time test.csv , + 00-06-30 changed"
    example_stamp = "[Convertor] $ adjust file by ms: change-ms test.csv , + 23400000 changed"
    example_start = "[Convertor] $ adjust file start time using date: change-start test.csv , 2024-03-12:09-00 2024-01-01:10-00 changed"
    example_start_ms = "[Convertor] $ adjust file start time using ms: change-start-ms test.csv , 2024-03-12:09-00 1701083201729 changed"

    print(usage)
    print(example_time)
    print(example_stamp)
    print(example_start)
    print(example_start_ms)

    exit(-1)
