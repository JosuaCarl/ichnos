import numpy as np
import sys, csv


def read_ts(filename):
    ts_data = {}

    with open(filename, 'r') as f:
        data = f.readlines()

    for load, row_i in zip(range(0, 100, 10), range(1,12)):
        ts_data[load] = float(data[row_i].strip().split(',')[3])

    ts_data[100] = float(data[14].strip().split(',')[3])  # power consumption with maximize stress test

    mem_idle = float(data[1].strip().split(',')[4])
    mem_max = float(data[13].strip().split(',')[4])  # memory power consumption with VMStress stress test

    return (ts_data, (mem_idle, mem_max))

def get_average_ts_files(path):
    paths = [path.replace('ITER', str(iteration)) for iteration in range(1, 4)]
    readings = {}
    mem_readings = []

    for path in paths:
        (path_data, mem_data) = read_ts(path)

        for load,val in path_data.items():
            if load in readings:
                readings[load].append(val)
            else:
                readings[load] = [val]

        avg_mem_draw = (mem_data[0] + mem_data[1]) / 2
        mem_readings.append(avg_mem_draw)

    data = {}

    for load,vals in readings.items():
        data[load] = sum(vals) / 3

    overall_avg_mem_draw = sum(mem_readings) / 3

    return (data, overall_avg_mem_draw)


def read_memory_draw():
    with open('memory.csv', 'r') as f:
        lines = [line.strip().split(',') for line in f.readlines()[1:]]

    no_load_draw = float(lines[0][3])
    load_draw_avg = sum([float(line[3]) for line in lines[1:]]) / 10

    return (round(no_load_draw, 3), round(load_draw_avg, 3))


class Polynomial:
    def __init__(self, coefficients):
        self.coeffs = coefficients

    def __str__(self):
        chunks = []
        for coeff in self.coeffs:
            if coeff == 0:
                continue
            chunks.append(self.format_coeff(coeff))
        return f"[ {', '.join(chunks)} ]"

    @staticmethod
    def format_coeff(coeff):
        return str(coeff)

    @staticmethod
    def format_power(power):
        return str(power) if power > 1 else ''


# Helper Functions
def make_model(filename):
    ts_path = f'ts/ts-ITER.csv'
    node_stats = {}
    (node_stats[filename], _) = get_average_ts_files(ts_path)
    x = range(0,110,10)
    y = node_stats[filename].values()
    y_arr = list(y)

    linear_v2_coef = np.polyfit(x, y_arr, 1)
    linear_v2 = np.poly1d(linear_v2_coef)
    model_linear_v2 = Polynomial(linear_v2)

    return (model_linear_v2, (min(y_arr), max(y_arr)))


# update to store in the format expected by ichnos / JSON ? or easily parseable record
# add versioning, i.e. date/timestamp for it, version like 1.0 and then increment -> 1.1 -- 1.11+
def write_output(filename, model, mem_draw, minmax, mem, gov):
    filename = f'{filename}-model.txt'
    (miiin, maaax) = minmax

    with open(filename, 'w') as f:
        f.write(f'"{filename}": {{\n')
        f.write(f'"{gov}": {{ "mem_draw": {mem_draw}, "linear": {model}, "min_watts": {miiin}, "max_watts": {maaax} }},\n')
        f.write('}\n')

        f.write(f'Memory Draw: {mem_draw / mem}\n')

    print(f'Model stored in file {filename}')


if __name__ == '__main__':
    args = sys.argv[1:]
    filename = args[0].strip()
    total_mem = int(args[1].strip())
    gov = args[2].strip()
    (model, minmax) = make_model(filename)
    mem_draw = read_memory_draw()
    write_output(filename, model, mem_draw, minmax, total_mem, gov)
