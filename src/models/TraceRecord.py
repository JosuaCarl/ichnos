from src.models.CarbonRecord import CarbonRecord


class TraceRecord:
    def __init__(self, fields, data, delimiter):
        self._raw = self.get_raw_data_map(fields, data, delimiter)
        self._id = self._raw['task_id']
        self._realtime = self._raw['realtime']

        if 'start' in self._raw:
            self._start = self._raw['start']
        else:
            self._start = None 

        if 'complete' in self._raw:
            self._complete = self._raw['complete']
        else:
            self._complete = None

        self._cpu_count = self._raw['cpus']
        self._cpu_usage = self._raw['%cpu']

        if 'cpu_model' in self._raw:
            self._cpu_model = self._raw['cpu_model']
        else:
            self._cpu_model = None

        self._memory = self._raw['memory']
        self._name = self._raw['name']
        self._task_id = self._raw['task_id']

        if 'hash' in self._raw:
            self._hash = self._raw['hash']
        else:
            self._hash = None

        self._process = self._raw['process']
        self._realtime = self._raw['realtime']
        self._submit = self._raw['submit']

    def get_raw_data_map(self, fields, data, delimiter):
        raw = {}

        for field, value in zip(fields.split(delimiter), data.split(delimiter)):
            value = value.strip()

            if field == "memory":  
                if value == '-':
                    value = None
                else:
                    value = float(value)
            elif field == "duration" or field == "realtime":  
                value = float(value)
            elif field == "%cpu":  # format x.y%
                if value[:-1] == '':
                    value = 0.0
                else:
                    value = float(value[:-1])
            elif field == "cpus":
                if value == '-':
                    value = 1
                else:
                    value = int(value)
            elif field == "rss":
                if value == '-':
                    value = None
                else:
                    value = float(value)

            raw[field] = value
    
        # where memory is not set, use rss (the amount of space of physical memory (RAM) held by a process)
        # further info: https://www.nextflow.io/docs/latest/metrics.html
        if raw['memory'] is None and 'rss' in raw:
            raw['memory'] = raw['rss']

        return raw 

    def make_carbon_record(self):
        return CarbonRecord(None, None, self._id, self._realtime, self._start, self._complete, self._cpu_count, None, self._cpu_usage, self._cpu_model, self._memory, self._name)

    def parse_realtime(self):
        return self._realtime  # 5s, 4s e.g. 

    def parse_duration(self):
        return self._realtime  # 4.9s, 4.9s like...

    def parse_start(self):
        return self._start  # timestamp, see CarbonRecord / diff calculation

    def parse_complete(self):
        return self._complete  # timestamp, see CarbonRecord / diff calculation

    def parse_cpu_percentage(self):
        return self._cpu_usage  # 117.7% has a %, check for nulls? 

    def parse_memory(self):
        return self._memory  # 4 GB check what others look like ? 

    def get_cpu_count(self):
        return self._cpu_count
    
    def get_cpu_model(self):
        return self._cpu_model

    def get_task_id(self):
        return self._task_id
    
    def get_hash(self):
        return self._hash

    def get_process(self):
        return self._process

    def get_realtime(self):
        return self._realtime

    def get_submit(self):
        return self._submit

    def get_complete(self):
        return self._complete

    def get_start(self):
        return self._start

    def __str__(self):
        return f"[TraceRecord: {str(self._raw)}]"
