import datetime as time
import copy

from src.models.TraceRecord import TraceRecord
from src.utils.Parsers import parse_trace_file
from src.Constants import FILE

# TODO: timezone conversion for non-utc times

def to_timestamp(ms):
    return time.datetime.fromtimestamp(float(ms) / 1000.0, tz=time.timezone.utc)

def get_tasks_by_hour_with_overhead(start_hour, end_hour, tasks):
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
            # full task is within this hour
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            # task ends within this hour (but starts in a previous hour)
            elif complete > i and complete < i + step and start < i:
                # add task from start of this hour until end of hour
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_realtime(complete - i)
                data.append(partial_task)
                runtimes.append(complete - i)
            # task starts within this hour (but ends in a later hour) -- OVERHEAD
            elif start > i and start < i + step and complete > i + step: 
                # add task from start to end of this hour
                partial_task = copy.deepcopy(task)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(i + step - start)
                data.append(partial_task)
                if (i + step - start) > hour_overhead:  # get the overhead for the longest task that starts now but ends later
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
            # task starts before hour and ends after this hour
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

    # task_overall_runtime = sum(runtimes)

    return (tasks_by_hour, overheads)

def get_tasks_by_interval_with_overhead(start_interval, end_interval, tasks, interval):
    tasks_by_hour = {}
    overheads = []
    runtimes = []

    step = interval * 60 * 1000  # interval minutes in ms
    i = start_interval - step  # start an interval before to be safe
    end_interval = end_interval + step  # finish an interval later to be safe

    while i <= end_interval:
        data = [] 
        hour_overhead = 0

        for task in tasks: 
            start = int(task.get_start())
            complete = int(task.get_complete())
            # full task is within this hour
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            # task ends within this hour (but starts in a previous hour)
            elif complete > i and complete < i + step and start < i:
                # add task from start of this hour until end of hour
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_realtime(complete - i)
                data.append(partial_task)
                runtimes.append(complete - i)
            # task starts within this hour (but ends in a later hour) -- OVERHEAD
            elif start > i and start < i + step and complete > i + step: 
                # add task from start to end of this hour
                partial_task = copy.deepcopy(task)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(i + step - start)
                data.append(partial_task)
                if (i + step - start) > hour_overhead:  # get the overhead for the longest task that starts now but ends later
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
            # task starts before hour and ends after this hour
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

    # task_overall_runtime = sum(runtimes)

    return (tasks_by_hour, overheads)

def to_closest_hour_ms(original):
    ts = to_timestamp(original)

    if ts.minute >= 30:
        if ts.hour + 1 == 24:
            # ts = ts.replace(hour=0, minute=0, second=0, microsecond=0, day=ts.day+1)
            ts = ts + time.timedelta(days=1)
            ts = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            ts = ts.replace(second=0, microsecond=0, minute=0, hour=ts.hour+1)
    else:
        ts = ts.replace(second=0, microsecond=0, minute=0)

    return int(ts.timestamp() * 1000)  # closest hour in ms

# round down to the closest interval
def to_closest_interval_ms(original, interval):
    ts = to_timestamp(original)
    ts = ts.replace(second=0, microsecond=0)
    ts = ts - time.timedelta(minutes=(ts.minute) % interval)
    return int(ts.timestamp() * 1000) 

def get_tasks_by_hour(tasks):
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

def get_tasks_by_interval(tasks, interval):
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

def extract_tasks_by_hour(filename):
    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]

    records = parse_trace_file(f"data/trace/{filename}.{FILE}")
    data_records = []

    for record in records:
        data = record.make_carbon_record()
        data_records.append(data)

    return get_tasks_by_hour(data_records)

def extract_tasks_by_interval(filename, interval):
    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]

    records = parse_trace_file(f"data/trace/{filename}.{FILE}")
    data_records = []

    for record in records:
        data = record.make_carbon_record()
        data_records.append(data)

    return get_tasks_by_interval(data_records, interval)

def get_hours(arr):
    hours = []
    prev = arr[0]
    i = 1

    while i < len(arr):
        if not (prev + 1 == arr[i]):  # if not consecutive, workflow halts and resumes
            hours.append(i - 1)  # add the overhead for the previous hour which will not finish by this hour
        prev = arr[i]
        i += 1

    return hours