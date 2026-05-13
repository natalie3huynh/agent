from datetime import date, timedelta
from typing import Optional
import re


def parse(s: str, today: Optional[date] = None) -> date:
    if today is None:
        today = date.today()

    s = s.strip().lower()

    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    if s.startswith("in "):
        return _parse_in_days(s, today)

    if s.endswith(" ago"):
        return _parse_ago(s, today)

    if s.startswith("next "):
        return _parse_next_day(s, today)

    if s.startswith("last "):
        return _parse_last_day(s, today)

    if s.startswith("this "):
        return _parse_this_day(s, today)

    if " days before " in s or " day before " in s:
        return _parse_days_before_date(s, today)

    if " days from " in s or " day from " in s:
        return _parse_days_from_date(s, today)

    return _parse_absolute_date(s, today)


def _parse_in_days(s: str, today: date) -> date:
    match = re.match(r"in (\d+) days?", s)
    if match:
        num = int(match.group(1))
        return today + timedelta(days=num)

    match = re.match(r"in (\d+) weeks?", s)
    if match:
        num = int(match.group(1))
        return today + timedelta(weeks=num)

    match = re.match(r"in (\d+) months?", s)
    if match:
        num = int(match.group(1))
        return _add_months(today, num)

    raise ValueError(f"Cannot parse: {s}")


def _parse_ago(s: str, today: date) -> date:
    match = re.match(r"(\d+) days? ago", s)
    if match:
        num = int(match.group(1))
        return today - timedelta(days=num)

    match = re.match(r"(\d+) weeks? ago", s)
    if match:
        num = int(match.group(1))
        return today - timedelta(weeks=num)

    match = re.match(r"(\d+) months? ago", s)
    if match:
        num = int(match.group(1))
        return _add_months(today, -num)

    raise ValueError(f"Cannot parse: {s}")


def _parse_next_day(s: str, today: date) -> date:
    day_name = s[5:].strip()
    target_weekday = _day_name_to_weekday(day_name)
    if target_weekday is None:
        raise ValueError(f"Cannot parse: {s}")

    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    return today + timedelta(days=days_ahead)


def _parse_last_day(s: str, today: date) -> date:
    day_name = s[5:].strip()
    target_weekday = _day_name_to_weekday(day_name)
    if target_weekday is None:
        raise ValueError(f"Cannot parse: {s}")

    days_ago = today.weekday() - target_weekday
    if days_ago < 0:
        days_ago += 7

    if days_ago == 0:
        days_ago = 7

    return today - timedelta(days=days_ago)


def _parse_this_day(s: str, today: date) -> date:
    day_name = s[5:].strip()
    target_weekday = _day_name_to_weekday(day_name)
    if target_weekday is None:
        raise ValueError(f"Cannot parse: {s}")

    days_ahead = target_weekday - today.weekday()
    if days_ahead < 0:
        days_ahead += 7

    return today + timedelta(days=days_ahead)


def _parse_days_before_date(s: str, today: date) -> date:
    match = re.match(r"(\d+) days? before (.+)", s)
    if match:
        num = int(match.group(1))
        date_str = match.group(2).strip()
        base_date = _parse_simple_date(date_str, today)
        if base_date is None:
            raise ValueError(f"Cannot parse: {s}")
        return base_date - timedelta(days=num)

    raise ValueError(f"Cannot parse: {s}")


def _parse_days_from_date(s: str, today: date) -> date:
    match = re.match(r"(\d+) days? from (.+)", s)
    if match:
        num = int(match.group(1))
        date_str = match.group(2).strip()
        base_date = _parse_simple_date(date_str, today)
        if base_date is None:
            raise ValueError(f"Cannot parse: {s}")
        return base_date + timedelta(days=num)

    raise ValueError(f"Cannot parse: {s}")


def _parse_absolute_date(s: str, today: date) -> date:
    parsed = _parse_simple_date(s, today)
    if parsed is not None:
        return parsed

    raise ValueError(f"Cannot parse: {s}")


def _parse_simple_date(s: str, today: date) -> Optional[date]:
    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    match = re.match(
        r"(\w+) (\d+)(?:st|nd|rd|th)?,? (\d{4})", s
    )
    if match:
        month_str = match.group(1).lower()
        day = int(match.group(2))
        year = int(match.group(3))
        if month_str in month_names:
            return date(year, month_names[month_str], day)

    match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return date(year, month, day)

    match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return date(year, month, day)

    return None


def _day_name_to_weekday(day_name: str) -> Optional[int]:
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    return days.get(day_name)


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, _days_in_month(year, month))
    return date(year, month, day)


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
