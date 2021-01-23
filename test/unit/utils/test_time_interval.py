import pytest
from datetime import datetime
from src.utils import time_interval

SIMPLE_DATE_FORMAT = '%Y-%m-%d'
LONG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class TestGetTimestampIntervalForStartingDate:
    def test_start_date_below_max_end_date(self):
        start_date = datetime.strptime('2020-01-01', SIMPLE_DATE_FORMAT)
        max_end_date = datetime.strptime('2020-01-10', SIMPLE_DATE_FORMAT)
        days_per_interval = 1

        expected = (
            datetime.strptime('2020-01-01 00:00:00', LONG_DATE_FORMAT), 
            datetime.strptime('2020-01-01 23:59:59', LONG_DATE_FORMAT)
        )

        result = time_interval.get_timestamp_interval_for_starting_date(start_date, max_end_date, days_per_interval)

        resulting_dates = (datetime.fromtimestamp(result[0]), datetime.fromtimestamp(result[1]))
        assert resulting_dates == expected


    def test_start_date_above_max_end_date(self):
        start_date = datetime.strptime('2020-01-01', SIMPLE_DATE_FORMAT)
        max_end_date = datetime.strptime('2020-01-03', SIMPLE_DATE_FORMAT)
        days_per_interval = 4

        expected = (
            datetime.strptime('2020-01-01 00:00:00', LONG_DATE_FORMAT), 
            datetime.strptime('2020-01-03 00:00:00', LONG_DATE_FORMAT)
        )

        result = time_interval.get_timestamp_interval_for_starting_date(start_date, max_end_date, days_per_interval)

        resulting_dates = (datetime.fromtimestamp(result[0]), datetime.fromtimestamp(result[1]))
        assert resulting_dates == expected

