from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
import re


# =========================
# PUBLIC API
# =========================

def parse(s: str, today: Optional[date] = None) -> date:
    if today is None:
        today = date.today()

    s = _normalize_ordinals(s.strip().lower())

    # -------------------------
    # simple keywords
    # -------------------------
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    # -------------------------
    # special phrases
    # -------------------------
    if s == "a week ago":
        return today - timedelta(weeks=1)
    if s == "a year from now":
        return _add_years(today, 1)
    if s == "two weeks ago":
        return today - timedelta(weeks=2)
    if s == "2 weeks from now":
        return today + timedelta(weeks=2)
    if s == "the day after tomorrow":
        return today + timedelta(days=2)

    # -------------------------
    # multi-unit BEFORE/AFTER (NEW FIX)
    # -------------------------
    if " before " in s:
        return _parse_multi(s, today, direction=-1)
    if " after " in s:
        return _parse_multi(s, today, direction=1)

    # -------------------------
    # relative patterns
    # -------------------------
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

    # -------------------------
    # single-unit before/after (kept for compatibility)
    # -------------------------
    if "days before" in s:
        return _parse_days_before(s)
    if "days after" in s:
        return _parse_days_after(s)
    if "days from" in s:
        return _parse_days_from(s)

    # -------------------------
    # absolute
    # -------------------------
    parsed = _parse_date(s)
    if parsed is not None:
        return parsed

    raise ValueError(f"Cannot parse: {s}")


# =========================
# MULTI-UNIT PARSING (FIX)
# =========================

def _parse_multi(s: str, today: date, direction: int) -> date:
    """
    Handles:
    - "2 years, 3 months before Dec. 1, 2025"
    - "1 year and 2 months after yesterday"
    """
    if " before " in s:
        left, base_str = s.split(" before ", 1)
        base = _resolve_base(base_str, today)
        return _apply_multi(left, base, -1)

    if " after " in s:
        left, base_str = s.split(" after ", 1)
        base = _resolve_base(base_str, today)
        return _apply_multi(left, base, 1)

    raise ValueError(f"Cannot parse: {s}")


def _resolve_base(s: str, today: date) -> date:
    s = s.strip()

    if s == "today":
        return today
    if s == "yesterday":
        return today - timedelta(days=1)
    if s == "tomorrow":
        return today + timedelta(days=1)

    parsed = _parse_date(s)
    if parsed is not None:
        return parsed

    raise ValueError(f"Cannot parse base: {s}")


def _apply_multi(expr: str, base: date, sign: int) -> date:
    """
    Parses:
    "2 years, 3 months"
    "1 year and 2 months"
    """
    parts = re.split(r",|and", expr)
    parts = [p.strip() for p in parts if p.strip()]

    result = base

    for p in parts:
        if m := re.fullmatch(r"(\d+) days?", p):
            result = result + timedelta(days=sign * int(m.group(1)))
        elif m := re.fullmatch(r"(\d+) weeks?", p):
            result = result + timedelta(weeks=sign * int(m.group(1)))
        elif m := re.fullmatch(r"(\d+) months?", p):
            result = _add_months(result, sign * int(m.group(1)))
        elif m := re.fullmatch(r"(\d+) years?", p):
            result = _add_years(result, sign * int(m.group(1)))
        else:
            raise ValueError(f"Invalid multi-unit: {p}")

    return result


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
# WEEKDAY LOGIC
# =========================

def _parse_next(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, True)


def _parse_last(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, False)


def _parse_this(s: str, today: date) -> date:
    return _weekday_offset(s[5:], today, True, allow_same=True)


def _weekday_offset(day: str, today: date, forward: bool, allow_same: bool = False) -> date:
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

def _normalize_ordinals(s: str) -> str:
    return re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)


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
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        return 28
    return 30
