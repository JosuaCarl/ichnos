from src.models.CarbonRecord import CarbonRecord

class TraceRecord:
    def __init__(self, fields: str, data: str, delimiter: str) -> None:
        self._raw = self.get_raw_data_map(fields, data, delimiter)
        self._id = self._raw['task_id']
        self._realtime = self._raw['realtime']
        self._start = self._raw.get('start')
        self._complete = self._raw.get('complete')
        self._cpu_count = self._raw['cpus']
        self._cpu_usage = self._raw['%cpu']
        self._cpu_model = self._raw.get('cpu_model')
        self._memory = self._raw['memory']
        self._name = self._raw['name']
        self._task_id = self._raw['task_id']
        self._hash = self._raw.get('hash')
        self._process = self._raw['process']
        self._realtime = self._raw['realtime']
        self._submit = self._raw['submit']

    def get_raw_data_map(self, fields: str, data: str, delimiter: str) -> dict:
        raw = {}
        for field, value in zip(fields.split(delimiter), data.split(delimiter)):
            value = value.strip()
            if field == "memory":
                value = None if value == '-' else float(value)
            elif field == "duration" or field == "realtime":
                value = float(value)
            elif field == "%cpu":  # format x.y%
                value = 0.0 if value[:-1] == '' else float(value[:-1])
            elif field == "cpus":
                value = 1 if value == '-' else int(value)
            elif field == "rss":
                value = None if value == '-' else float(value)
            raw[field] = value
        # where memory is not set, use rss
        if raw['memory'] is None and 'rss' in raw:
            raw['memory'] = raw['rss']
        return raw 

    def make_carbon_record(self) -> CarbonRecord:
        return CarbonRecord(
            energy=None, 
            co2e=None, 
            id=self._id, 
            realtime=self._realtime, 
            start=self._start, 
            complete=self._complete, 
            core_count=self._cpu_count, 
            cpu_powerdraw=None, 
            cpu_usage=self._cpu_usage, 
            cpu_model=self._cpu_model, 
            memory=self._memory, 
            name=self._name
        )

    @property
    def realtime(self) -> float:
        return self._realtime

    @property
    def duration(self) -> float:
        return self._realtime

    @property
    def start(self):
        return self._start

    @property
    def complete(self):
        return self._complete

    @property
    def cpu_percentage(self) -> float:
        return self._cpu_usage

    @property
    def memory(self):
        return self._memory

    @property
    def cpu_count(self) -> int:
        return self._cpu_count

    @property
    def cpu_model(self):
        return self._cpu_model

    @property
    def task_id(self):
        return self._task_id

    @property
    def hash_value(self):
        return self._hash

    @property
    def process(self):
        return self._process

    @property
    def realtime(self):
        return self._realtime

    @property
    def submit(self):
        return self._submit

    @property
    def complete(self):
        return self._complete

    @property
    def start(self):
        return self._start

    def __str__(self) -> str:
        return f"[TraceRecord: {str(self._raw)}]"
