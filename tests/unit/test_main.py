"""Unit tests for app/main.py (API endpoints)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models import ClockUpdate


def _add_update(
    db,
    msg_id: int,
    time_value: str,
    content: str,
    created_at: datetime | None = None,
    image_data: str | None = None,
):
    update = ClockUpdate(
        message_id=msg_id,
        content=content,
        time_value=time_value,
        image_data=image_data,
        created_at=created_at or datetime.now(UTC),
    )
    db.add(update)
    db.commit()
    return update


def test_root_endpoint(test_client):
    resp = test_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Dooms Deal Clock API"
    assert data["status"] == "running"


def test_health_endpoint(test_client):
    resp = test_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "dooms-deal-clock"
    assert "version" in data


def test_latest_404_when_no_updates(test_client):
    resp = test_client.get("/api/clock/latest")
    assert resp.status_code == 404


def test_latest_returns_latest_update(test_client, test_db_session):
    # Older
    _add_update(test_db_session, 1, "10:00", "First", datetime.now(UTC) - timedelta(hours=1))
    # Newer
    newest = _add_update(test_db_session, 2, "11:00", "Second", datetime.now(UTC), image_data="YmFzZTY0")

    resp = test_client.get("/api/clock/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["message_id"] == newest.message_id
    assert data["time"] == newest.time_value
    assert data["content"] == newest.content
    assert data["image_data"] == newest.image_data
    assert "created_at" in data


def test_history_pagination_and_order(test_client, test_db_session):
    now = datetime.now(UTC)
    _add_update(test_db_session, 101, "10:00", "A", now - timedelta(minutes=3))
    _add_update(test_db_session, 102, "11:00", "B", now - timedelta(minutes=2))
    _add_update(test_db_session, 103, "12:00", "C", now - timedelta(minutes=1))

    resp = test_client.get("/api/clock/history?limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert data["total_count"] == 3
    assert len(data["updates"]) == 2
    # Most recent first
    assert data["updates"][0]["message_id"] == 103
    assert data["updates"][1]["message_id"] == 102


@pytest.mark.asyncio
async def test_fetch_endpoint_success(test_client, monkeypatch):
    import app.main as main_module

    async def fake_fetch(db):
        return 3

    monkeypatch.setattr(main_module.clock_service, "fetch_and_store_updates", fake_fetch, raising=True)

    resp = test_client.post("/api/clock/fetch")
    assert resp.status_code == 200
    data = resp.json()
    assert data["updates_count"] == 3
    assert "Successfully fetched" in data["message"]


@pytest.mark.asyncio
async def test_fetch_endpoint_failure_returns_500(test_client, monkeypatch):
    import app.main as main_module

    async def fake_fetch(db):
        raise RuntimeError("boom")

    monkeypatch.setattr(main_module.clock_service, "fetch_and_store_updates", fake_fetch, raising=True)

    resp = test_client.post("/api/clock/fetch")
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_reload_endpoint_deletes_and_refetches(test_client, test_db_session, monkeypatch):
    # Insert existing record
    _add_update(test_db_session, 777, "09:00", "Old", datetime.now(UTC))

    import app.main as main_module

    async def fake_fetch(db):
        return 1

    monkeypatch.setattr(main_module.clock_service, "fetch_and_store_updates", fake_fetch, raising=True)

    resp = test_client.post("/api/clock/reload/777")
    assert resp.status_code == 200
    data = resp.json()
    assert data["updates_count"] == 1
    assert data["message_id"] == 777
    assert "Successfully reloaded" in data["message"]


@pytest.mark.asyncio
async def test_reload_endpoint_error_returns_500(test_client, monkeypatch):
    import app.main as main_module

    async def fake_fetch(db):
        raise RuntimeError("fetch error")

    monkeypatch.setattr(main_module.clock_service, "fetch_and_store_updates", fake_fetch, raising=True)

    resp = test_client.post("/api/clock/reload/123")
    assert resp.status_code == 500

