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

    # simple keywords
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    # special phrases
    if s == "a week ago":
        return today - timedelta(weeks=1)
    if s == "a year from now":
        return _add_years(today, 1)
    if s == "two weeks ago":
        return today - timedelta(weeks=2)
    if s == "2 weeks from now":
        return today + timedelta(weeks=2)

    # compound expressions FIRST (important fix)
    if " and " in s or "," in s:
        parsed = _parse_compound(s, today)
        if parsed is not None:
            return parsed

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

    # before / after patterns
    if " before " in s:
        return _parse_before(s, today)

    if " after " in s:
        return _parse_after(s, today)

    if " from " in s:
        return _parse_from(s, today)

    # absolute date formats
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
# COMPOUND PARSING (NEW FIX)
# =========================

def _parse_compound(s: str, today: date) -> Optional[date]:
    base = today

    parts = re.split(r",| and ", s)

    for part in parts:
        part = part.strip()

        if not part:
            continue

        # before/after/date anchor
        if " before " in part:
            base = _apply_before(part, base)
        elif " after " in part:
            base = _apply_after(part, base)
        elif " from " in part:
            base = _apply_from(part, base)
        else:
            base = _apply_unit(part, base)

    return base


def _apply_unit(part: str, base: date) -> date:
    if m := re.fullmatch(r"(\d+) days?", part):
        return base + timedelta(days=int(m.group(1)))
    if m := re.fullmatch(r"(\d+) weeks?", part):
        return base + timedelta(weeks=int(m.group(1)))
    if m := re.fullmatch(r"(\d+) months?", part):
        return _add_months(base, int(m.group(1)))
    if m := re.fullmatch(r"(\d+) years?", part):
        return _add_years(base, int(m.group(1)))
    raise ValueError(part)


# =========================
# RELATIVE: IN / AGO
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
    raise ValueError(s)


def _parse_ago(s: str, today: date) -> date:
    if m := re.fullmatch(r"(\d+) days? ago", s):
        return today - timedelta(days=int(m.group(1)))
    if m := re.fullmatch(r"(\d+) weeks? ago", s):
        return today - timedelta(weeks=int(m.group(1)))
    if m := re.fullmatch(r"(\d+) months? ago", s):
        return _add_months(today, -int(m.group(1)))
    if m := re.fullmatch(r"(\d+) years? ago", s):
        return _add_years(today, -int(m.group(1)))
    raise ValueError(s)


# =========================
# BEFORE / AFTER / FROM
# =========================

def _parse_before(s: str, today: date) -> date:
    m = re.fullmatch(r"(\d+) (days?|weeks?|months?|years?) before (.+)", s)
    if not m:
        raise ValueError(s)

    value = int(m.group(1))
    unit = m.group(2)
    base = _parse_date(m.group(3))
    if base is None:
        raise ValueError(s)

    return _apply_unit(f"{value} {unit}", base)


def _parse_after(s: str, today: date) -> date:
    m = re.fullmatch(r"(\d+) (days?|weeks?|months?|years?) after (.+)", s)
    if not m:
        raise ValueError(s)

    value = int(m.group(1))
    unit = m.group(2)
    base = _parse_date(m.group(3))
    if base is None:
        raise ValueError(s)

    if unit.startswith("day"):
        return base + timedelta(days=value)
    if unit.startswith("week"):
        return base + timedelta(weeks=value)
    if unit.startswith("month"):
        return _add_months(base, value)
    if unit.startswith("year"):
        return _add_years(base, value)

    raise ValueError(s)


def _parse_from(s: str, today: date) -> date:
    m = re.fullmatch(r"(\d+) (days?|weeks?|months?|years?) from (.+)", s)
    if not m:
        raise ValueError(s)

    value = int(m.group(1))
    unit = m.group(2)
    base = _parse_date(m.group(3))
    if base is None:
        raise ValueError(s)

    return _apply_after(f"{value} {unit} after {m.group(3)}", today)


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
