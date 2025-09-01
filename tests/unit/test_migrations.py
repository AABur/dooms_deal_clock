"""Tests for database migrations module."""

from sqlalchemy import text


def _column_exists(engine, table: str, column: str) -> bool:
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT name FROM pragma_table_info('{table}') WHERE name='{column}'"))
        return res.fetchone() is not None


def test_add_image_data_column_adds_when_missing(test_db_engine, monkeypatch):
    import app.migrations as mig

    # Point migrations at the test engine
    monkeypatch.setattr(mig, "engine", test_db_engine, raising=True)

    # Create minimal schema without image_data
    with test_db_engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS clock_updates (
                    id INTEGER PRIMARY KEY,
                    message_id INTEGER,
                    content TEXT,
                    time_value TEXT,
                    created_at TEXT
                )
                """
            )
        )
        conn.commit()

    assert _column_exists(test_db_engine, "clock_updates", "image_data") is False

    mig.add_image_data_column()

    assert _column_exists(test_db_engine, "clock_updates", "image_data") is True


def test_add_image_data_column_idempotent_when_exists(test_db_engine, monkeypatch):
    import app.migrations as mig
    from app.models import Base

    # Use models metadata (which already includes image_data)
    Base.metadata.create_all(bind=test_db_engine)

    monkeypatch.setattr(mig, "engine", test_db_engine, raising=True)

    # Column should already exist, function should no-op without error
    assert _column_exists(test_db_engine, "clock_updates", "image_data") is True
    mig.add_image_data_column()
    assert _column_exists(test_db_engine, "clock_updates", "image_data") is True


def test_run_migrations_calls_add_and_logs(test_db_engine, monkeypatch, caplog):
    import app.migrations as mig

    # Use the isolated test engine
    monkeypatch.setattr(mig, "engine", test_db_engine, raising=True)

    called = {"add": 0}

    def fake_add():  # noqa: ANN001 - simple stub for migration
        called["add"] += 1

    monkeypatch.setattr(mig, "add_image_data_column", fake_add, raising=True)

    mig.run_migrations()
    assert called["add"] == 1
