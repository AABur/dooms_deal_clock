"""Tests for telegram_api/client.py (one module → one test file)."""

import base64
import types

import pytest

from app.telegram_api.client import TelegramService


@pytest.fixture
def telegram_service():
    return TelegramService()


def test_service_init(telegram_service):
    assert telegram_service.client is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("🕐 23:42 - Дедлайн приближается!", "23:42"),
        ("Time is 9:30 AM", "9:30"),
        ("Meeting at 14:15", "14:15"),
        ("Start at 9:45", "9:45"),
        ("🔔 7:30 reminder", "7:30"),
        ("Appointment at 15.30", "15.30"),
        ("🕒 12.45 meeting", "12.45"),
    ],
)
def test_extract_time_positive_patterns(telegram_service, text, expected):
    assert telegram_service.extract_time_from_message(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("No time here", None),
        ("Just some text", None),
        ("Numbers 123 456", None),
    ],
)
def test_extract_time_no_match(telegram_service, text, expected):
    assert telegram_service.extract_time_from_message(text) is expected


def test_extract_time_multiple_times_returns_first(telegram_service):
    assert telegram_service.extract_time_from_message("From 9:30 to 17:45") == "9:30"
    assert telegram_service.extract_time_from_message("🕐 14:20 and also 16:35") == "14:20"


def test_extract_time_mixed_formats(telegram_service):
    assert telegram_service.extract_time_from_message("At 12:30 or maybe 14.45") == "12:30"
    assert telegram_service.extract_time_from_message("Meeting at 14.30 today") == "14.30"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Price: 25:99", "25:99"),  # pattern matches even if semantically invalid
        ("Code: 123:456", "23:45"),  # finds substring
        ("Version 1.2.3", None),
        ("", None),
        ("::", None),
        ("..", None),
        ("12:34", "12:34"),
        ("Time: 23:59", "23:59"),
    ],
)
def test_extract_time_edge_and_invalid_cases(telegram_service, text, expected):
    result = telegram_service.extract_time_from_message(text)
    if expected is None:
        assert result is None
    else:
        assert result == expected


def test_service_instance_isolation():
    s1 = TelegramService()
    s2 = TelegramService()
    assert s1 is not s2
    assert s1.client is None and s2.client is None


@pytest.mark.asyncio
async def test__get_client_creates_and_reuses(mocker):
    from typing import Any

    from app.telegram_api import client as client_module

    created: dict[str, Any] = {"count": 0, "args": None}

    class FakeClient:
        async def start(self, *args, **kwargs):  # pragma: no cover - not used here
            return None

    def fake_telegram_client(session_name, api_id, api_hash):  # noqa: ANN001 - simple stub
        created["count"] += 1
        created["args"] = (session_name, api_id, api_hash)
        return FakeClient()

    mocker.patch.object(client_module, "TelegramClient", side_effect=fake_telegram_client)
    mocker.patch.object(client_module.config, "TELEGRAM_API_ID", "id")
    mocker.patch.object(client_module.config, "TELEGRAM_API_HASH", "hash")

    svc = client_module.TelegramService()
    c1 = svc._get_client()
    c2 = svc._get_client()

    assert c1 is c2
    assert created["count"] == 1
    assert created["args"][0] == "dooms_deal_session"


@pytest.mark.asyncio
async def test_connect_and_disconnect(mocker):
    from typing import Any

    from app.telegram_api import client as client_module

    started: dict[str, Any] = {"phone": None, "disconnects": 0}

    class FakeClient:
        async def start(self, phone=None):
            started["phone"] = phone

        async def disconnect(self):
            started["disconnects"] += 1

    mocker.patch.object(client_module, "TelegramClient", return_value=FakeClient())
    mocker.patch.object(client_module.config, "TELEGRAM_API_ID", "id")
    mocker.patch.object(client_module.config, "TELEGRAM_API_HASH", "hash")
    mocker.patch.object(client_module.config, "TELEGRAM_PHONE", "+10000000000")

    svc = client_module.TelegramService()
    await svc.connect()
    assert started["phone"] == "+10000000000"

    await svc.disconnect()
    assert started["disconnects"] == 1

    svc.client = None
    await svc.disconnect()
    assert started["disconnects"] == 1


@pytest.mark.asyncio
async def test_get_latest_messages_success_and_error(mocker):
    from app.telegram_api import client as client_module

    class FakeClient:
        def __init__(self):
            self._raise = False

        def iter_messages(self, channel, limit=10):  # type: ignore[override]
            if self._raise:

                async def _err_gen():
                    if False:  # pragma: no cover
                        yield None
                    raise RuntimeError("boom")

                return _err_gen()

            async def gen():
                for i in range(3):
                    msg = types.SimpleNamespace(id=i + 1, text=f"msg {i + 1}")
                    yield msg

            return gen()

    fake = FakeClient()
    mocker.patch.object(client_module, "TelegramClient", return_value=fake)
    mocker.patch.object(client_module.config, "TELEGRAM_API_ID", "id")
    mocker.patch.object(client_module.config, "TELEGRAM_API_HASH", "hash")

    svc = client_module.TelegramService()
    msgs = await svc.get_latest_messages(limit=5)
    assert len(msgs) == 3

    fake._raise = True
    msgs = await svc.get_latest_messages(limit=5)
    assert msgs == []


@pytest.mark.asyncio
async def test_get_channel_info_success_and_error(mocker):
    from app.telegram_api import client as client_module

    class Entity:
        id = 42
        title = "Chan"
        username = "chan_user"
        participants_count = 7

    class FakeClient:
        async def get_entity(self, _):
            return Entity()

    mocker.patch.object(client_module, "TelegramClient", return_value=FakeClient())
    mocker.patch.object(client_module.config, "TELEGRAM_API_ID", "id")
    mocker.patch.object(client_module.config, "TELEGRAM_API_HASH", "hash")

    svc = client_module.TelegramService()
    info = await svc.get_channel_info()
    assert info == {
        "id": 42,
        "title": "Chan",
        "username": "chan_user",
        "participants_count": 7,
    }

    class BadClient:
        async def get_entity(self, _):
            raise RuntimeError("bad")

    mocker.patch.object(client_module, "TelegramClient", return_value=BadClient())
    svc2 = client_module.TelegramService()
    assert await svc2.get_channel_info() is None


@pytest.mark.asyncio
async def test_get_message_image_data_happy_and_error(mocker):
    from app.telegram_api import client as client_module

    class PhotoType:  # acts as MessageMediaPhoto
        pass

    mocker.patch.object(client_module, "MessageMediaPhoto", PhotoType)

    class FakeClient:
        async def download_media(self, message, file):  # noqa: ARG002
            file.write(b"hello")

    mocker.patch.object(client_module, "TelegramClient", return_value=FakeClient())
    mocker.patch.object(client_module.config, "TELEGRAM_API_ID", "id")
    mocker.patch.object(client_module.config, "TELEGRAM_API_HASH", "hash")

    svc = client_module.TelegramService()

    class Msg:
        id = 5
        media = PhotoType()

    data = await svc.get_message_image_data(Msg())
    assert data == base64.b64encode(b"hello").decode()

    class BadClient:
        async def download_media(self, message, file):  # noqa: ARG002
            raise RuntimeError("dl error")

    mocker.patch.object(client_module, "TelegramClient", return_value=BadClient())
    bad = client_module.TelegramService()
    assert await bad.get_message_image_data(Msg()) is None


@pytest.mark.asyncio
async def test_get_message_image_data_returns_none_without_media():
    service = TelegramService()

    class Message:
        media = None

    result = await service.get_message_image_data(Message())
    assert result is None


@pytest.mark.asyncio
async def test_get_message_image_data_returns_none_with_non_photo_media():
    service = TelegramService()

    class Message:
        media = object()  # Not a MessageMediaPhoto

    result = await service.get_message_image_data(Message())
    assert result is None
