import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from backfill import fridays_between


def dt(year, month, day):
    return datetime(year, month, day, tzinfo=timezone.utc)


class TestFridaysBetween:
    def test_returns_fridays_only(self):
        result = fridays_between(dt(2026, 1, 1), dt(2026, 1, 31))
        for d in result:
            assert d.weekday() == 4  # 4 = Friday

    def test_from_date_is_friday(self):
        # 2026-01-02 is Friday
        result = fridays_between(dt(2026, 1, 2), dt(2026, 1, 16))
        assert result[0] == dt(2026, 1, 2)

    def test_from_date_not_friday(self):
        # 2026-01-01 is Thursday, first Friday is Jan 2
        result = fridays_between(dt(2026, 1, 1), dt(2026, 1, 16))
        assert result[0] == dt(2026, 1, 2)

    def test_correct_count(self):
        # Jan 2, 9, 16 = 3 Fridays
        result = fridays_between(dt(2026, 1, 1), dt(2026, 1, 16))
        assert len(result) == 3

    def test_weekly_interval(self):
        result = fridays_between(dt(2026, 1, 1), dt(2026, 2, 28))
        for i in range(1, len(result)):
            diff = (result[i] - result[i - 1]).days
            assert diff == 7

    def test_to_date_before_first_friday_returns_empty(self):
        # from=Jan 3 (Sat), to=Jan 7 (Wed) → no Friday in range
        result = fridays_between(dt(2026, 1, 3), dt(2026, 1, 7))
        assert result == []

    def test_from_equals_to_friday(self):
        # from=to=Friday → [that Friday]
        result = fridays_between(dt(2026, 1, 2), dt(2026, 1, 2))
        assert len(result) == 1
        assert result[0] == dt(2026, 1, 2)
