from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
import re


def parse(s: str, today: Optional[date] = None) -> date:
    if today is None:
        today = date.today()

    s = s.strip().lower()
    s = _normalize_ordinals(s)

    # simple keywords
    if s == "today":
        return today

    if s == "tomorrow":
        return today + timedelta(days=1)

    if s == "yesterday":
        return today - timedelta(days=1)

    # special natural phrases
    if s == "a week ago":
        return today - timedelta(weeks=1)

    if s == "a year from now":
        return _add_years(today, 1)

    if s == "two weeks ago":
        return today - timedelta(weeks=2)

    if s == "2 weeks from now":
        return today + timedelta(weeks=2)

    # relative patterns
    if s.startswith("in "):
        return _parse_in(s, today)

    if s.endswith(" ago"):
        return _parse_ago(s, today)

    if s.startswith("next "):
        return _parse_next(s, today)

    if s.startswith("last "):
        return _parse_last(s, today)

    if s.startswith("this "):
        return _parse_this(s, today)

    # BEFORE / AFTER
    if " before " in s:
        return _parse_multi_before(s, today)

    if " after " in s:
        return _parse_multi_after(s, today)

    if " day from " in s or " days from " in s:
        return _parse_days_from(s, today)

    if " year from " in s or " years from " in s:
        return _parse_years_from(s, today)

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
# SPLIT HELPER
# =========================


def _split_units(left: str) -> list[str]:
    """
    Supports:
    - '1 year and 2 months'
    - '2 years, 3 months'
    """
    return [c.strip() for c in re.split(r",| and ", left) if c.strip()]


# =========================
# BASE DATE HELPER
# =========================


def _parse_base_date(s: str, today: date) -> Optional[date]:
    s = s.strip().lower()

    if s == "today":
        return today

    if s == "tomorrow":
        return today + timedelta(days=1)

    if s == "yesterday":
        return today - timedelta(days=1)

    return _parse_date(s)


# =========================
# RELATIVE
# =========================


def _parse_in(s: str, today: date) -> date:
    if m := re.fullmatch(r"in (\d+) days?", s):
        return today + timedelta(days=int(m.group(1)))

    if m := re.fullmatch(r"in (\d+) weeks?", s):
        return today + timedelta(weeks=int(m.group(1)))

    if m := re.fullmatch(r"in (\d+) months?", s):
        return _add_months(today, int(m.group(1)))

    if m := re.fullmatch(r"in (\d+) years?", s):
        return _add_years(today, int(m.group(1)))

    raise ValueError(f"Cannot parse: {s}")


def _parse_ago(s: str, today: date) -> date:
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
# WEEKDAYS
# =========================


def _parse_next(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, True)


def _parse_last(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, False)


def _parse_this(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, True, allow_same=True)


def _weekday_offset(
    day_name: str,
    today: date,
    forward: bool,
    allow_same: bool = False,
) -> date:
    target = _weekday(day_name)

    if target is None:
        raise ValueError(f"Unknown weekday: {day_name}")

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
# MULTI BEFORE / AFTER
# =========================


def _parse_multi_before(s: str, today: date) -> date:
    m = re.fullmatch(r"(.+?) before (.+)", s)
    if not m:
        raise ValueError(f"Cannot parse: {s}")

    left, right = m.group(1), m.group(2)

    base = _parse_base_date(right, today)
    if base is None:
        raise ValueError(f"Cannot parse: {s}")

    years = months = weeks = days = 0

    for chunk in _split_units(left):
        if m := re.fullmatch(r"(\d+) years?", chunk):
            years = int(m.group(1))
        elif m := re.fullmatch(r"(\d+) months?", chunk):
            months = int(m.group(1))
        elif m := re.fullmatch(r"(\d+) weeks?", chunk):
            weeks = int(m.group(1))
        elif m := re.fullmatch(r"(\d+) days?", chunk):
            days = int(m.group(1))
        else:
            raise ValueError(f"Cannot parse: {s}")

    result = base
    result = _add_years(result, -years)
    result = _add_months(result, -months)
    result -= timedelta(weeks=weeks)
    result -= timedelta(days=days)

    return result


def _parse_multi_after(s: str, today: date) -> date:
    m = re.fullmatch(r"(.+?) after (.+)", s)
    if not m:
        raise ValueError(f"Cannot parse: {s}")

    left, right = m.group(1), m.group(2)

    base = _parse_base_date(right, today)
    if base is None:
        raise ValueError(f"Cannot parse: {s}")

    years = months = weeks = days = 0

    for chunk in _split_units(left):
        if m := re.fullmatch(r"(\d+) years?", chunk):
            years = int(m.group(1))
        elif m := re.fullmatch(r"(\d+) months?", chunk):
            months = int(m.group(1))
        elif m := re.fullmatch(r"(\d+) weeks?", chunk):
            weeks = int(m.group(1))
        elif m := re.fullmatch(r"(\d+) days?", chunk):
            days = int(m.group(1))
        else:
            raise ValueError(f"Cannot parse: {s}")

    result = base
    result = _add_years(result, years)
    result = _add_months(result, months)
    result += timedelta(weeks=weeks)
    result += timedelta(days=days)

    return result


# =========================
# FROM HELPERS
# =========================


def _parse_days_from(s: str, today: date) -> date:
    m = re.fullmatch(r"(\d+) days? from (.+)", s)
    if not m:
        raise ValueError(s)

    base = _parse_base_date(m.group(2), today)
    if base is None:
        raise ValueError(s)

    return base + timedelta(days=int(m.group(1)))


def _parse_years_from(s: str, today: date) -> date:
    m = re.fullmatch(r"(\d+) years? from (.+)", s)
    if not m:
        raise ValueError(s)

    base = _parse_base_date(m.group(2), today)
    if base is None:
        raise ValueError(s)

    return _add_years(base, int(m.group(1)))


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

    return 29 if month == 2 else 28
