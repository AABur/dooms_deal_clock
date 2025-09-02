import os
import threading
import time
from contextlib import contextmanager
import importlib
import socket

import pytest


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@contextmanager
def _run_uvicorn(app, port: int):
    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait server up
    import http.client

    for _ in range(50):
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=0.2)
            conn.request("GET", "/api/health")
            resp = conn.getresponse()
            if resp.status in (200, 404):
                break
        except Exception:
            time.sleep(0.1)
        finally:
            try:
                conn.close()
            except Exception:
                pass
    try:
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=3)


@pytest.fixture
def serve_app(monkeypatch):
    """Factory to serve app with custom message content/image for UI tests."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    def _serve(content: str, image_data: str | None = None):
        import app.main as main_module
        importlib.reload(main_module)

        class Obj:
            def __init__(self, **kw):
                self.__dict__.update(kw)

        fake_update = Obj(
            id=1,
            time_value="23:56:05",
            content=content,
            image_data=image_data,
            created_at=__import__("datetime").datetime.now(),
            message_id=1,
        )

        class FakeClock:
            def get_latest_update(self, db):  # noqa: ANN001
                return fake_update

        main_module.clock_service = FakeClock()  # type: ignore
        from app.main import app

        port = _free_port()
        return app, port

    return _serve

