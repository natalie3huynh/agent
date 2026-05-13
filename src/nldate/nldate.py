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

    # ------------------------
    # special phrases (must come first)
    # ------------------------
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    if s == "the day before yesterday":
        return today - timedelta(days=2)
    if s == "the day after tomorrow":
        return today + timedelta(days=2)

    if s == "a week ago":
        return today - timedelta(weeks=1)
    if s == "a year from now":
        return _add_years(today, 1)
    if s == "two weeks ago":
        return today - timedelta(weeks=2)
    if s == "2 weeks from now":
        return today + timedelta(weeks=2)

    # ------------------------
    # compound expressions (NEW KEY FEATURE)
    # ------------------------
    if _is_compound(s):
        return _parse_compound(s, today)

    # ------------------------
    # relative patterns
    # ------------------------
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

    # ------------------------
    # before / after
    # ------------------------
    if " before " in s:
        return _parse_before(s)

    if " after " in s:
        return _parse_after(s)

    if " from " in s:
        return _parse_from(s)

    # ------------------------
    # absolute date
    # ------------------------
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
# COMPOUND EXPRESSIONS
# =========================

def _is_compound(s: str) -> bool:
    return (" and " in s) or ("," in s)


def _parse_compound(s: str, today: date) -> date:
    """
    Handles:
    - 1 year and 2 months after yesterday
    - 2 years, 3 months before Dec. 1, 2025
    """

    if " before " in s:
        base_str = s.split(" before ", 1)[1]
        base = _parse_date(base_str)
        if base is None:
            raise ValueError(s)

        parts = re.split(r",| and ", s.split(" before ")[0])
        return _apply_units(base, parts, subtract=True)

    if " after " in s:
        base_str = s.split(" after ", 1)[1]
        base = _parse_date(base_str) or _parse_relative_base(base_str, today)
        if base is None:
            raise ValueError(s)

        parts = re.split(r",| and ", s.split(" after ")[0])
        return _apply_units(base, parts, subtract=False)

    raise ValueError(s)


def _apply_units(base: date, parts: list[str], subtract: bool) -> date:
    result = base

    for p in parts:
        p = p.strip()
        if not p:
            continue

        if m := re.fullmatch(r"(\d+)\s+days?", p):
            delta = timedelta(days=int(m.group(1)))

        elif m := re.fullmatch(r"(\d+)\s+weeks?", p):
            delta = timedelta(weeks=int(m.group(1)))

        elif m := re.fullmatch(r"(\d+)\s+months?", p):
            result = _add_months(result, -int(m.group(1)) if subtract else int(m.group(1)))
            continue

        elif m := re.fullmatch(r"(\d+)\s+years?", p):
            result = _add_years(result, -int(m.group(1)) if subtract else int(m.group(1)))
            continue

        else:
            raise ValueError(p)

        if subtract:
            result -= delta
        else:
            result += delta

    return result


def _parse_relative_base(s: str, today: date) -> date | None:
    s = s.strip()

    if s == "today":
        return today
    if s == "yesterday":
        return today - timedelta(days=1)
    if s == "tomorrow":
        return today + timedelta(days=1)

    return _parse_date(s)


# =========================
# IN / AGO
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

def _parse_before(s: str) -> date:
    m = re.fullmatch(r"(\d+)\s+days?\s+before\s+(.+)", s)
    if not m:
        raise ValueError(s)
    base = _parse_date(m.group(2))
    if base is None:
        raise ValueError(s)
    return base - timedelta(days=int(m.group(1)))


def _parse_after(s: str) -> date:
    m = re.fullmatch(r"(\d+)\s+days?\s+after\s+(.+)", s)
    if not m:
        raise ValueError(s)
    base = _parse_date(m.group(2))
    if base is None:
        raise ValueError(s)
    return base + timedelta(days=int(m.group(1)))


def _parse_from(s: str) -> date:
    m = re.fullmatch(r"(\d+)\s+days?\s+from\s+(.+)", s)
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

    if m := re.fullmatch(r"([a-z]+\.?) (\d+), (\d{4})", s):
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
