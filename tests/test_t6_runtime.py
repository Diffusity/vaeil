"""Runtime Clock adapter preserves local-date and aware-UTC timestamp semantics."""
from datetime import datetime, timezone, timedelta


def test_runtime_age_date_is_local_while_session_time_is_utc(monkeypatch):
    from vaeil import runtime
    local = datetime(2026, 11, 15, 1, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    utc = datetime(2026, 11, 14, 19, 30, tzinfo=timezone.utc)
    class FixedDateTime:
        @staticmethod
        def now(tz=None):
            return local if tz is None else utc
    monkeypatch.setattr(runtime, "datetime", FixedDateTime)
    clock = runtime.RuntimeClock()
    assert clock.today() == local.date()
    assert clock.now() == utc and clock.now().utcoffset() == timedelta(0)
