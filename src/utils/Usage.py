def print_usage_exit_TemporalInterrupt():
    usage = "$ python -m src.scripts.TemporalInterrupt <ci-file-name> <pue> <memory_coefficient> <min-watts> <max-watts>"
    example = "$ python -m src.scripts.TemporalInterrupt ci 1.0 0.392 65 219"

    print(usage)
    print(example)
    exit(-1)
