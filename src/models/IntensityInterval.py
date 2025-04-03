class IntensityInterval:
    def __init__(self, date: str, start: str, end: str, forecast: int, actual: int, index: str) -> None:
        self._date = str(date)
        self._start = str(start)
        self._end = str(end)
        self._forecast = int(forecast) if forecast is not None else 0
        self._actual = int(actual)
        self._index = str(index)

    @property
    def date(self) -> str:
        return self._date

    @property
    def start(self) -> str:
        return self._start

    @property
    def end(self) -> str:
        return self._end

    @property
    def forecast(self) -> int:
        return self._forecast

    @property
    def actual(self) -> int:
        return self._actual

    @property
    def index(self) -> str:
        return self._index

    def __str__(self) -> str:
        return f"{self._date},{self._start},{self._end},{self._forecast},{self._actual},{self._index}"

def make_intensity_interval(start: str, end: str, actual: int) -> IntensityInterval:
    return IntensityInterval(None, start, end, None, actual, None)
