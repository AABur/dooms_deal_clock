"""Tests for app/services/background_tasks.py (one module → one test file)."""

import pytest

from app.services.background_tasks import BackgroundTaskService, background_service


def test_service_init():
    svc = BackgroundTaskService()
    assert svc.clock_service is not None
    assert svc.is_running is False
    assert svc.task is None


def test_global_instance_exists_and_initial_state():
    assert background_service is not None
    assert isinstance(background_service, BackgroundTaskService)
    assert background_service.is_running is False
    assert background_service.task is None
    assert background_service.clock_service is not None


def test_global_instance_independence():
    new_service = BackgroundTaskService()
    assert new_service is not background_service
    assert new_service.is_running is False
    assert new_service.task is None


@pytest.mark.asyncio
async def test_start_periodic_updates_runs_single_cycle(monkeypatch):
    from app.services import background_tasks as bg_module

    svc = BackgroundTaskService()

    # Speed up loop and ensure it stops after one iteration
    monkeypatch.setattr(bg_module.config, "UPDATE_INTERVAL_SECONDS", 0)

    async def fake_sleep(_):  # noqa: ANN001 - test stub
        svc.is_running = False

    import asyncio as _asyncio

    monkeypatch.setattr(_asyncio, "sleep", fake_sleep, raising=True)

    async def fake_fetch(db):  # noqa: ANN001 - test stub
        return 2

    monkeypatch.setattr(svc.clock_service, "fetch_and_store_updates", fake_fetch, raising=True)

    await svc.start_periodic_updates()
    assert svc.is_running is False


def test_start_idempotent(monkeypatch):
    import asyncio as _asyncio

    created = {"count": 0}

    class FakeTask:
        def done(self):
            return False

    def fake_create_task(coro):  # noqa: ANN001 - simple stub
        created["count"] += 1
        try:
            coro.close()
        except Exception:
            pass
        return FakeTask()

    monkeypatch.setattr(_asyncio, "create_task", fake_create_task, raising=True)

    svc = BackgroundTaskService()
    svc.start()
    svc.start()  # second start should not create a new task

    assert created["count"] == 1


def test_start_and_stop_background_task(monkeypatch):
    cancelled = {"value": False}

    class FakeTask:
        def done(self):
            return False

        def cancel(self):
            cancelled["value"] = True

    created = {"count": 0}

    def fake_create_task(coro):  # noqa: ANN001 - simple stub
        created["count"] += 1
        try:
            coro.close()
        except Exception:
            pass
        return FakeTask()

    import asyncio as _asyncio

    monkeypatch.setattr(_asyncio, "create_task", fake_create_task, raising=True)

    svc = BackgroundTaskService()

    assert svc.is_running is False
    assert svc.task is None
    assert svc.is_task_running() is False

    svc.start()
    assert svc.task is not None
    assert created["count"] == 1

    svc.stop()
    assert svc.is_running is False
    assert cancelled["value"] is True
    assert svc.is_task_running() is False


def test_start_recreates_when_task_done(monkeypatch):
    created = {"count": 0}

    class DoneTask:
        def done(self):
            return True

    class RunningTask:
        def done(self):
            return False

    def fake_create_task(coro):  # noqa: ANN001 - test stub
        created["count"] += 1
        try:
            coro.close()
        except Exception:
            pass
        return DoneTask() if created["count"] == 1 else RunningTask()

    import asyncio as _asyncio

    monkeypatch.setattr(_asyncio, "create_task", fake_create_task, raising=True)

    svc = BackgroundTaskService()
    svc.start()  # first call returns done task
    svc.start()  # second call should create a new task since previous is done

    assert created["count"] == 2


def test_stop_when_task_already_done(monkeypatch):
    cancelled = {"value": False}

    class DoneTask:
        def done(self):
            return True

        def cancel(self):  # pragma: no cover - should not be called
            cancelled["value"] = True

    import asyncio as _asyncio

    def _create(coro):
        try:
            coro.close()
        except Exception:
            pass
        return DoneTask()

    monkeypatch.setattr(_asyncio, "create_task", _create, raising=True)

    svc = BackgroundTaskService()
    svc.start()
    svc.stop()
    assert svc.is_running is False
    assert cancelled["value"] is False


def test_is_task_running_matrix():
    class RunningTask:
        def done(self):
            return False

    class DoneTask:
        def done(self):
            return True

    svc = BackgroundTaskService()

    svc.is_running = True
    svc.task = None
    assert bool(svc.is_task_running()) is False

    svc.task = DoneTask()  # type: ignore[assignment]
    assert bool(svc.is_task_running()) is False

    svc.is_running = False
    svc.task = RunningTask()  # type: ignore[assignment]
    assert bool(svc.is_task_running()) is False

    svc.is_running = True
    assert bool(svc.is_task_running()) is True
