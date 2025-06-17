# Export Carbon Intensity
# Uses hourly data retrieved from the Electricity Maps Data Portal: https://www.electricitymaps.com/data-portal


# Imports
from src.utils.Usage import print_usage_exit_ExportCarbonIntensity as print_usage_exit

import sys
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import date, timedelta


# Constants
cols = ['datetime_utc', 'country', 'zone', 'zone_id', 'ci', 'lca', 'low_carbon_%', 'renewable_%', 'source', 'estimated', 'method']
weekdays_23 = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
weekdays_24 = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekdays_23_x = np.repeat(weekdays_23, 24)
weekdays_24_x = np.repeat(weekdays_24, 24)
weekdays_vals_23 = np.resize(weekdays_23_x, 8760)
weeksdays_vals_24 = np.resize(weekdays_24_x, 8784)
day_starts = [1,25,49,73,97,121,145]
days = range(1,366,1)
hour_cols = [str(time).zfill(2) for time in range(0,24,1)]
month_cols = [str(month).zfill(2) for month in range(1,13,1)]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
month_starts = [1,32,61,92,122,153,183,214,245,275,306,336]
START = "start"
END = "end"
YEAR = "year"
MONTH = "month"
DAY = "day"
DF = "df"
GB = "gb"
DE = "de"
CA = "ca"
TX = "tx"
ZA = "za"
TYO = "tyo"
NSW = "nsw"
RECOGNISED_DFS = [GB, DE, CA, TX, ZA, TYO, NSW]


# Functions
def prepare_region_gb(filepath, date_sep="/"):
    df = pd.read_csv(filepath, names=cols, header=None, skiprows=1)

    if "2024" in filepath:
        df['weekday'] = weeksdays_vals_24
    else:
        df['weekday'] = weekdays_vals_23
    df[['date', 'hour']] = df['datetime_utc'].str.split(' ', n=1, expand=True)
    df['hour'] = df['hour'].replace(':00:00', ':00')
    df[['day', 'month', 'year']] = df['date'].str.split(date_sep, n=2, expand=True)
    df['date'] = df[['year', 'month', 'day']].apply("-".join, axis=1)
    df.drop(['country', 'zone', 'zone_id', 'source', 'estimated', 'method', 'year', 'datetime_utc'], inplace=True, axis=1)
    return df


def prepare_region(filepath, date_sep="-"):
    df = pd.read_csv(filepath, names=cols, header=None, skiprows=1)

    if "2024" in filepath:
        df['weekday'] = weeksdays_vals_24
    else:
        df['weekday'] = weekdays_vals_23

    df[['date', 'hour']] = df['datetime_utc'].str.split(' ', n=1, expand=True)
    df['hour'] = df['hour'].str.replace(':00:00', ':00')
    df[['year', 'month', 'day']] = df['date'].str.split(date_sep, n=2, expand=True)
    df['date'] = df[['year', 'month', 'day']].apply("-".join, axis=1)
    df.drop(['country', 'zone', 'zone_id', 'source', 'estimated', 'method', 'year', 'datetime_utc'], inplace=True, axis=1)
    return df


def get_end(time):
    if str(time) == "23:00":
        return "00:00"
    else:
        hour = str(int(str(time).split(":")[0]) + 1).zfill(2)
        return f"{hour}:00"


def get_data_for_day(df, day_of_month):
    data = df.groupby(['month', 'day'], sort=False, as_index=False)
    data_day = data.get_group(day_of_month)
    data_day["start"] = data_day["hour"]
    data_day["end"] = data_day["start"].apply(get_end)
    data_day["actual"] = data_day["ci_direct"]
    data_day.drop(["hour", "ci_direct"], inplace=True, axis=1)
    data_day = data_day[["date", "start", "end", "actual"]]

    return data_day


def fetch_carbon_intensity_data(intervals):
    return []


def get_days(start, end):
    start_day = date(int(start[YEAR]), int(start[MONTH]), int(start[DAY]))
    end_day = date(int(end[YEAR]), int(end[MONTH]), int(end[DAY]))
    iter_day = start_day
    days = []

    while iter_day <= end_day:
        days.append((str(iter_day.month).zfill(2), str(iter_day.day).zfill(2)))
        iter_day += timedelta(days=1)

    return days


def write_carbon_intensity_data(data, name):
    filepath = "data/intensity/"
    filename = f"avg-{name}.csv"

    data[['date','hour','day','month','weekday','ci']].to_csv(filepath + filename, sep=",", index=False, encoding="utf-8")

    return filepath + filename


def export_carbon_intensity(dfs):
    for (df, name) in dfs:
        output_file = write_carbon_intensity_data(df, name)
        print(f"[ExportCarbonIntensity] Successfully Exported CI Data to [{output_file}]")

    return output_file


def setup_data():
    # GB Data
    gb_23_ci_df = prepare_region_gb('data/emaps/GB_2023_hourly.csv')
    gb_24_ci_df = prepare_region('data/emaps/GB_2024_hourly.csv')
    # Germany Data
    de_23_ci_df = prepare_region('data/emaps/DE_2023_hourly.csv')
    de_24_ci_df = prepare_region('data/emaps/DE_2024_hourly.csv')
    # California Data
    ca_23_ci_df = prepare_region('data/emaps/US-CAL-CISO_2023_hourly.csv')
    ca_24_ci_df = prepare_region('data/emaps/US-CAL-CISO_2024_hourly.csv')
    # Texas Data
    tx_23_ci_df = prepare_region('data/emaps/US-TEX-ERCO_2023_hourly.csv')
    tx_24_ci_df = prepare_region('data/emaps/US-TEX-ERCO_2024_hourly.csv')
    # South Africa Data
    za_23_ci_df = prepare_region('data/emaps/ZA_2023_hourly.csv')
    za_24_ci_df = prepare_region('data/emaps/ZA_2024_hourly.csv')
    # Tokyo Data
    tyo_23_ci_df = prepare_region('data/emaps/JP-TK_2023_hourly.csv')
    tyo_24_ci_df = prepare_region('data/emaps/JP-TK_2024_hourly.csv')
    # New South Wales
    nsw_23_ci_df = prepare_region('data/emaps/AU-NSW_2023_hourly.csv')
    nsw_24_ci_df = prepare_region('data/emaps/AU-NSW_2024_hourly.csv')
    return [(gb_23_ci_df, 'gb-2023'), (gb_24_ci_df, 'gb-2024'), (de_23_ci_df, 'de-2023'), (de_24_ci_df, 'de-2024'), 
            (ca_23_ci_df, 'ca-2023'), (ca_24_ci_df, 'ca-2024'), (tx_23_ci_df, 'tx-2023'), (tx_24_ci_df, 'tx-2024'), 
            (za_23_ci_df, 'za-2023'), (za_24_ci_df, 'za-2024'), (tyo_23_ci_df, 'tyo-2023'), (tyo_24_ci_df, 'tyo-2024'), 
            (nsw_23_ci_df, 'nsw-2023'), (nsw_24_ci_df, 'nsw-2024')]


# Main Script
if __name__ == "__main__":
    dfs = setup_data()
    export_carbon_intensity(dfs)
