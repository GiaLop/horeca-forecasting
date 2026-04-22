"""
utils_forecast.py
-----------------
Utility functions specific to the HoReCa forecasting pipeline.
Imported in notebooks as:  import src.utils_forecast as ut_f
"""

from datetime import timedelta
import pandas as pd


def compute_ponte(date_range, holidays_set):
    """
    Identify bridge days (ponti) given a date range and a set of holiday dates.

    A ponte is a weekday that falls between a holiday and a weekend, making it
    rational to take the day off to create a long weekend. Two cases are handled:

    Case 1 — LATERAL bridge:
        A weekday adjacent (±1 day) to BOTH a weekday holiday and a weekend day.
        Example: Thursday is a holiday → Friday is ponte (Thu holiday + Sat weekend).

    Case 2 — CENTRAL bridge:
        A weekday flanked by weekday holidays on BOTH sides within ±2 days.
        Example: Monday is a holiday + Wednesday is a holiday → Tuesday between
        them is a ponte centrale.

    Key rule: only WEEKDAY holidays trigger a ponte.
        A holiday falling on Sat/Sun already coincides with a rest day —
        there is no gap to bridge, so weekend holidays are excluded from detection.

    Parameters
    ----------
    date_range : pd.DatetimeIndex
        Full date range to evaluate (e.g. pd.date_range('2023-01-01', '2024-12-31')).
    holidays_set : set of datetime.date
        Set of holiday dates (Italian national + provincial, or extended with Swiss).

    Returns
    -------
    set of datetime.date
        Set of dates identified as ponte days.
    """
    def is_weekday_holiday(d):
        """True only if d is a holiday AND falls on a weekday (Mon–Fri)."""
        return d in holidays_set and d.weekday() < 5

    ponte_set = set()

    for d in date_range:
        date_obj = d.date()

        # A weekend day or holiday itself cannot be a ponte
        if date_obj.weekday() >= 5 or date_obj in holidays_set:
            continue

        left1  = date_obj - timedelta(days=1)
        right1 = date_obj + timedelta(days=1)
        left2  = date_obj - timedelta(days=2)
        right2 = date_obj + timedelta(days=2)
        adj_days = [left1, right1]

        adj_holiday = any(is_weekday_holiday(n) for n in adj_days)
        adj_weekend = any(n.weekday() >= 5 for n in adj_days)

        # Case 1: lateral — weekday holiday on one side, weekend on the other
        if adj_holiday and adj_weekend:
            ponte_set.add(date_obj)
            continue

        # Case 2: central — weekday holidays on both sides within ±2 days
        left_holiday  = is_weekday_holiday(left1) or is_weekday_holiday(left2)
        right_holiday = is_weekday_holiday(right1) or is_weekday_holiday(right2)
        if left_holiday and right_holiday:
            ponte_set.add(date_obj)

    return ponte_set


def get_season(month):
    """
    Map a month number to its meteorological season (Northern Hemisphere).

    Parameters
    ----------
    month : int
        Month number (1–12).

    Returns
    -------
    str
        One of: 'winter', 'spring', 'summer', 'autumn'.
    """
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'


def days(start, end):
    """
    Return a list of ISO date strings (YYYY-MM-DD) for an inclusive date range.

    Parameters
    ----------
    start : str
        Start date in YYYY-MM-DD format.
    end : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    list of str
        One string per day from start to end inclusive.

    Example
    -------
    >>> days('2023-04-18', '2023-04-20')
    ['2023-04-18', '2023-04-19', '2023-04-20']
    """
    return [str(d.date()) for d in pd.date_range(start=start, end=end, freq='D')]
