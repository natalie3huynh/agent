from datetime import date
import pytest
from nldate import parse


class TestRelativeDays:
    def test_today(self):
        today = date(2025, 1, 15)
        assert parse("today", today) == today

    def test_tomorrow(self):
        today = date(2025, 1, 15)
        assert parse("tomorrow", today) == date(2025, 1, 16)

    def test_yesterday(self):
        today = date(2025, 1, 15)
        assert parse("yesterday", today) == date(2025, 1, 14)

    def test_in_x_days(self):
        today = date(2025, 1, 15)
        assert parse("in 3 days", today) == date(2025, 1, 18)

    def test_x_days_ago(self):
        today = date(2025, 1, 15)
        assert parse("5 days ago", today) == date(2025, 1, 10)

    def test_in_x_weeks(self):
        today = date(2025, 1, 15)
        assert parse("in 2 weeks", today) == date(2025, 1, 29)

    def test_x_weeks_ago(self):
        today = date(2025, 1, 15)
        assert parse("3 weeks ago", today) == date(2024, 12, 25)


class TestDayOfWeek:
    def test_next_tuesday(self):
        today = date(2025, 1, 15)
        assert parse("next Tuesday", today) == date(2025, 1, 21)

    def test_last_monday(self):
        today = date(2025, 1, 15)
        assert parse("last Monday", today) == date(2025, 1, 13)

    def test_this_thursday(self):
        today = date(2025, 1, 15)
        assert parse("this Thursday", today) == date(2025, 1, 16)


class TestAbsoluteDates:
    def test_month_day_year(self):
        today = date(2025, 1, 15)
        assert parse("December 1st, 2025", today) == date(2025, 12, 1)

    def test_mdy_date(self):
        today = date(2025, 1, 15)
        assert parse("1/15/2026", today) == date(2026, 1, 15)

    def test_iso_date(self):
        today = date(2025, 1, 15)
        assert parse("2025-06-15", today) == date(2025, 6, 15)


class TestDaysBefore:
    def test_days_before_date(self):
        today = date(2025, 12, 1)
        assert parse("5 days before December 1st, 2025", today) == date(2025, 11, 26)

    def test_days_from_date(self):
        today = date(2025, 12, 1)
        assert parse("10 days from December 1st, 2025", today) == date(2025, 12, 11)


class TestEdgeCases:
    def test_today_default(self):
        result = parse("today")
        assert result == date.today()

    def test_in_months(self):
        today = date(2025, 1, 15)
        assert parse("in 3 months", today) == date(2025, 4, 15)

    def test_months_ago(self):
        today = date(2025, 1, 15)
        assert parse("2 months ago", today) == date(2024, 11, 15)

    def test_invalid_raises(self):
        today = date(2025, 1, 15)
        with pytest.raises(ValueError):
            parse("not a valid date", today)
