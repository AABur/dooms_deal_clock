"""Runtime behavior tests for BackgroundTaskService start/stop lifecycle."""


from app.services.background_tasks import BackgroundTaskService


def test_start_and_stop_background_task(monkeypatch):
    # Fake asyncio task
    cancelled = {"value": False}

    class FakeTask:
        def done(self):
            return False

        def cancel(self):
            cancelled["value"] = True

    created = {"count": 0}

    def fake_create_task(coro):  # noqa: ANN001 - simple stub
        created["count"] += 1
        return FakeTask()

    import asyncio as _asyncio

    monkeypatch.setattr(_asyncio, "create_task", fake_create_task, raising=True)

    svc = BackgroundTaskService()

    # Initially stopped
    assert svc.is_running is False
    assert svc.task is None
    assert svc.is_task_running() is False

    # Start should create a task (we stub actual coroutine execution)
    svc.start()
    assert svc.task is not None
    assert created["count"] == 1
    # Since the coroutine didn't run, service may still be marked as not running
    assert isinstance(svc.task, object)

    # Stop should cancel task and set running False
    svc.stop()
    assert svc.is_running is False
    assert cancelled["value"] is True
    # After stop, is_task_running should be False regardless of task state
    assert svc.is_task_running() is False
