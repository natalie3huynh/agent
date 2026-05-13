from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
import re


# =========================
# PUBLIC FUNCTION
# =========================

def parse(s: str, today: Optional[date] = None) -> date:
    if today is None:
        today = date.today()

    s = s.strip().lower()
    s = _normalize_ordinals(s)

    # -----------------------
    # simple cases
    # -----------------------
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    if s == "a week ago":
        return today - timedelta(weeks=1)
    if s == "two weeks ago":
        return today - timedelta(weeks=2)
    if s == "a year from now":
        return _add_years(today, 1)
    if s == "2 weeks from now":
        return today + timedelta(weeks=2)

    # -----------------------
    # relative patterns
    # -----------------------
    if s.startswith("in "):
        return _parse_in(s)

    if s.endswith(" ago"):
        return _parse_ago(s)

    if s.startswith("next "):
        return _parse_next(s)

    if s.startswith("last "):
        return _parse_last(s)

    if s.startswith("this "):
        return _parse_this(s)

    # -----------------------
    # before / after (UPDATED)
    # -----------------------
    if " before " in s:
        return _parse_compound(s, sign=-1)

    if " after " in s:
        return _parse_compound(s, sign=1)

    if " from " in s:
        return _parse_from(s)

    # -----------------------
    # absolute dates
    # -----------------------
    parsed = _parse_date(s)
    if parsed is not None:
        return parsed

    raise ValueError(f"Cannot parse: {s}")


# =========================
# NORMALIZATION
# =========================

def _normalize_ordinals(s: str) -> str:
    return re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)


# =========================
# IN / AGO
# =========================

def _parse_in(s: str) -> date:
    if m := re.fullmatch(r"in (\d+) days?", s):
        return date.today() + timedelta(days=int(m.group(1)))
    if m := re.fullmatch(r"in (\d+) weeks?", s):
        return date.today() + timedelta(weeks=int(m.group(1)))
    if m := re.fullmatch(r"in (\d+) months?", s):
        return _add_months(date.today(), int(m.group(1)))
    if m := re.fullmatch(r"in (\d+) years?", s):
        return _add_years(date.today(), int(m.group(1)))
    raise ValueError(s)


def _parse_ago(s: str) -> date:
    if m := re.fullmatch(r"(\d+) days? ago", s):
        return date.today() - timedelta(days=int(m.group(1)))
    if m := re.fullmatch(r"(\d+) weeks? ago", s):
        return date.today() - timedelta(weeks=int(m.group(1)))
    if m := re.fullmatch(r"(\d+) months? ago", s):
        return _add_months(date.today(), -int(m.group(1)))
    if m := re.fullmatch(r"(\d+) years? ago", s):
        return _add_years(date.today(), -int(m.group(1)))
    raise ValueError(s)


# =========================
# WEEKDAY PARSING
# =========================

def _parse_next(s: str) -> date:
    return _weekday_offset(s[5:], True)

def _parse_last(s: str) -> date:
    return _weekday_offset(s[5:], False)

def _parse_this(s: str) -> date:
    return _weekday_offset(s[5:], True, allow_same=True)


def _weekday_offset(day: str, forward: bool, allow_same: bool = False) -> date:
    target = _weekday(day)
    if target is None:
        raise ValueError(day)

    today = date.today()
    diff = target - today.weekday()

    if forward:
        if diff < 0 or (diff == 0 and not allow_same):
            diff += 7
        return today + timedelta(days=diff)

    diff = today.weekday() - target
    if diff <= 0:
        diff += 7
    return today - timedelta(days=diff)


# =========================
# COMPOUND BEFORE / AFTER (NEW CORE FIX)
# =========================

def _parse_compound(s: str, sign: int) -> date:
    """
    Handles:
    - 2 years, 3 months before Dec. 1, 2025
    - 2 years 3 days after 2025-12-04
    """

    m = re.fullmatch(r"(.+?) (before|after) (.+)", s)
    if not m:
        raise ValueError(s)

    left, _, right = m.group(1), m.group(2), m.group(3)

    base = _parse_date(right)
    if base is None:
        raise ValueError(s)

    years = 0
    months = 0
    days = 0

    tokens = re.split(r",|\s+", left)

    i = 0
    while i < len(tokens):
        if not tokens[i]:
            i += 1
            continue

        num = int(tokens[i])
        unit = tokens[i + 1] if i + 1 < len(tokens) else ""

        if "year" in unit:
            years += num
        elif "month" in unit:
            months += num
        elif "week" in unit:
            days += num * 7
        elif "day" in unit:
            days += num

        i += 2

    base = _add_years(base, sign * years)
    base = _add_months(base, sign * months)
    base = base + timedelta(days=sign * days)

    return base


# supports "X days from Y"
def _parse_from(s: str) -> date:
    m = re.fullmatch(r"(\d+) days? from (.+)", s)
    if not m:
        raise ValueError(s)

    base = _parse_date(m.group(2))
    if base is None:
        raise ValueError(s)

    return base + timedelta(days=int(m.group(1)))


# =========================
# ABSOLUTE DATES
# =========================

def _parse_date(s: str) -> Optional[date]:
    s = _normalize_ordinals(s)

    if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s):
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s):
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

    if m := re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", s):
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    if m := re.fullmatch(r"([a-z]+\.?) (\d+),? (\d{4})", s):
        month = _month_to_int(m.group(1))
        if month is None:
            return None
        return date(int(m.group(3)), month, int(m.group(2)))

    return None


# =========================
# HELPERS
# =========================

def _month_to_int(name: str) -> Optional[int]:
    name = name.rstrip(".")
    return {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }.get(name)


def _weekday(name: str) -> Optional[int]:
    return {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }.get(name)


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, _days_in_month(year, month))
    return date(year, month, day)


def _add_years(d: date, years: int) -> date:
    try:
        return date(d.year + years, d.month, d.day)
    except ValueError:
        return date(d.year + years, d.month, 28)


def _days_in_month(year: int, month: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if month == 2:
        return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
    return 30
