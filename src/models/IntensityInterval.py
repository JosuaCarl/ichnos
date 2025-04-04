"""
Module: IntensityInterval
This module defines the IntensityInterval class which represents an interval 
of carbon intensity data with associated forecast, actual values, and index.
"""

class IntensityInterval:
    """
    Represents a carbon intensity interval.
    
    Attributes:
        date (str): The date of the interval.
        start (str): The start time.
        end (str): The end time.
        forecast (int): Forecasted carbon intensity.
        actual (int): Actual carbon intensity.
        index (str): An identifier/index for the interval.
    """
    def __init__(self, date: str, start: str, end: str, forecast: int, actual: int, index: str) -> None:
        """
        Initialize an IntensityInterval.
        
        :param date: The date of the interval.
        :param start: The start time.
        :param end: The end time.
        :param forecast: Forecasted carbon intensity.
        :param actual: Actual carbon intensity.
        :param index: The index of the interval.
        """
        self._date = str(date)
        self._start = str(start)
        self._end = str(end)
        self._forecast = int(forecast) if forecast is not None else 0
        self._actual = int(actual)
        self._index = str(index)

    @property
    def date(self) -> str:
        """Return the date of the interval."""
        return self._date

    @property
    def start(self) -> str:
        """Return the start time of the interval."""
        return self._start

    @property
    def end(self) -> str:
        """Return the end time of the interval."""
        return self._end

    @property
    def forecast(self) -> int:
        """Return the forecasted carbon intensity."""
        return self._forecast

    @property
    def actual(self) -> int:
        """Return the actual carbon intensity."""
        return self._actual

    @property
    def index(self) -> str:
        """Return the index of the interval."""
        return self._index

    def __str__(self) -> str:
        """
        Return a CSV-like string representation of the intensity interval.
        """
        return f"{self._date},{self._start},{self._end},{self._forecast},{self._actual},{self._index}"

def make_intensity_interval(start: str, end: str, actual: int) -> IntensityInterval:
    """
    Factory function to create an IntensityInterval instance.
    
    :param start: The start time.
    :param end: The end time.
    :param actual: The actual carbon intensity.
    :return: An IntensityInterval instance.
    """
    return IntensityInterval(None, start, end, None, actual, None)
