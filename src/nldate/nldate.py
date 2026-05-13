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

    # -----------------------
    # relative patterns
    # -----------------------
    if s.startswith("in ") or s.endswith(" from now"):
        return _parse_in(s, today)

    if s.endswith(" ago"):
        return _parse_ago(s, today)

    if s.startswith("next "):
        return _parse_next(s, today)

    if s.startswith("last "):
        return _parse_last(s, today)

    if s.startswith("this "):
        return _parse_this(s, today)

    # -----------------------
    # before / after forms
    # -----------------------
    if " days before " in s or " day before " in s:
        return _parse_days_before(s)

    if " days from " in s or " day from " in s:
        return _parse_days_from(s)

    if " years before " in s or " year before " in s:
        return _parse_years_before(s)

    if " years from " in s or " year from " in s:
        return _parse_years_from(s)

    # -----------------------
    # absolute date formats
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
# RELATIVE: IN / AGO
# =========================


def _parse_in(s: str, today: date) -> date:
    if s == "in a day":
        return today + timedelta(days=1)

    if s == "in a week":
        return today + timedelta(weeks=1)

    if s == "in a month":
        return _add_months(today, 1)

    if s == "in a year":
        return _add_years(today, 1)

    if m := re.fullmatch(r"in (\d+) days?", s):
        return today + timedelta(days=int(m.group(1)))

    if m := re.fullmatch(r"in (\d+) weeks?", s):
        return today + timedelta(weeks=int(m.group(1)))

    if m := re.fullmatch(r"(\d+) weeks? from now", s):
        return today + timedelta(weeks=int(m.group(1)))

    if m := re.fullmatch(r"in (\d+) months?", s):
        return _add_months(today, int(m.group(1)))

    if m := re.fullmatch(r"in (\d+) years?", s):
        return _add_years(today, int(m.group(1)))

    raise ValueError(f"Cannot parse: {s}")


def _parse_ago(s: str, today: date) -> date:
    if s == "a day ago":
        return today - timedelta(days=1)

    if s == "a week ago":
        return today - timedelta(weeks=1)

    if s == "a month ago":
        return _add_months(today, -1)

    if s == "a year ago":
        return _add_years(today, -1)

    if s == "two weeks ago":
        return today - timedelta(weeks=2)

    if m := re.fullmatch(r"(\d+) days? ago", s):
        return today - timedelta(days=int(m.group(1)))

    if m := re.fullmatch(r"(\d+) weeks? ago", s):
        return today - timedelta(weeks=int(m.group(1)))

    if m := re.fullmatch(r"(\d+) months? ago", s):
        return _add_months(today, -int(m.group(1)))

    if m := re.fullmatch(r"(\d+) years? ago", s):
        return _add_years(today, -int(m.group(1)))

    raise ValueError(f"Cannot parse: {s}")


# =========================
# WEEKDAY LOGIC
# =========================


def _parse_next(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, forward=True)


def _parse_last(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, forward=False)


def _parse_this(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, forward=True, allow_same=True)


def _weekday_offset(
    day: str,
    today: date,
    forward: bool,
    allow_same: bool = False,
) -> date:
    target = _weekday(day)

    if target is None:
        raise ValueError(f"Unknown weekday: {day}")

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
# BEFORE / FROM
# =========================


def _parse_days_before(s: str) -> date:
    m = re.fullmatch(r"(\d+) days? before (.+)", s)

    if not m:
        raise ValueError(s)

    base = _parse_date(m.group(2))

    if base is None:
        raise ValueError(s)

    return base - timedelta(days=int(m.group(1)))


def _parse_days_from(s: str) -> date:
    m = re.fullmatch(r"(\d+) days? from (.+)", s)

    if not m:
        raise ValueError(s)

    base = _parse_date(m.group(2))

    if base is None:
        raise ValueError(s)

    return base + timedelta(days=int(m.group(1)))


def _parse_years_before(s: str) -> date:
    m = re.fullmatch(r"(\d+) years? before (.+)", s)

    if not m:
        raise ValueError(s)

    base = _parse_date(m.group(2))

    if base is None:
        raise ValueError(s)

    return _add_years(base, -int(m.group(1)))


def _parse_years_from(s: str) -> date:
    m = re.fullmatch(r"(\d+) years? from (.+)", s)

    if not m:
        raise ValueError(s)

    base = _parse_date(m.group(2))

    if base is None:
        raise ValueError(s)

    return _add_years(base, int(m.group(1)))


# =========================
# ABSOLUTE DATES
# =========================


def _parse_date(s: str) -> Optional[date]:
    s = _normalize_ordinals(s)

    # YYYY-MM-DD
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s):
        return date(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
        )

    # MM/DD/YYYY
    if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s):
        return date(
            int(m.group(3)),
            int(m.group(1)),
            int(m.group(2)),
        )

    # YYYY/MM/DD
    if m := re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", s):
        return date(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
        )

    # Month formats
    # Supports:
    # Dec 1 2025
    # Dec. 1, 2025
    # December 1st, 2025
    if m := re.fullmatch(r"([a-z]+)\.? (\d+),? (\d{4})", s):
        month = _month_to_int(m.group(1))

        if month is None:
            return None

        return date(
            int(m.group(3)),
            month,
            int(m.group(2)),
        )

    return None


# =========================
# HELPERS
# =========================


def _month_to_int(name: str) -> Optional[int]:
    name = name.rstrip(".")

    return {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
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
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29

        return 28

    return 30
