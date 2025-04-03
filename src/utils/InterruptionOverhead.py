import copy

# TODO: this function was in TemporalInterrupt but was not used
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
            start = int(task.start)
            complete = int(task.complete)
            # full task is within this hour
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            # task ends within this hour (but starts in a previous hour)
            elif complete > i and complete < i + step and start < i:
                # add task from start of this hour until end of hour
                partial_task = copy.deepcopy(task)
                partial_task.start = i
                partial_task.realtime = complete - i
                data.append(partial_task)
                runtimes.append(complete - i)
            # task starts within this hour (but ends in a later hour) -- OVERHEAD
            elif start > i and start < i + step and complete > i + step: 
                # add task from start to end of this hour
                partial_task = copy.deepcopy(task)
                partial_task.complete = i + step
                partial_task.realtime = i + step - start
                data.append(partial_task)
                if (i + step - start) > hour_overhead:  # get the overhead for the longest task that starts now but ends later
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
            # task starts before hour and ends after this hour
            elif start < i and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.start = i
                partial_task.complete = i + step
                partial_task.realtime = step
                data.append(partial_task)
                runtimes.append(step)

        tasks_by_hour[i] = data
        overheads.append(hour_overhead)
        i += step

    return (tasks_by_hour, overheads)
