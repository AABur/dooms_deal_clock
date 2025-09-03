"""Unit tests for app/utils/db.py."""


def test_create_tables_function_calls_metadata(mocker):
    from app.utils.db import create_tables

    mock_base = mocker.patch("app.utils.db.Base")
    mock_metadata = mocker.MagicMock()
    mock_base.metadata = mock_metadata

    create_tables()
    mock_metadata.create_all.assert_called_once()


def test_get_db_function_workflow(mocker):
    from app.utils.db import get_db

    mock_session_local = mocker.patch("app.utils.db.SessionLocal")
    mock_session = mocker.MagicMock()
    mock_session_local.return_value = mock_session

    db_gen = get_db()
    session = next(db_gen)
    assert session == mock_session
    try:
        next(db_gen)
    except StopIteration:
        pass
    mock_session_local.assert_called_once()
    mock_session.close.assert_called_once()


def test_clock_update_repr_method_direct():
    from app.utils.db import ClockUpdate

    update = ClockUpdate()
    update.id = 42  # type: ignore[assignment]
    update.time_value = "12:34"  # type: ignore[assignment]
    repr_str = repr(update)
    assert "ClockUpdate" in repr_str
    assert "id=42" in repr_str
    assert "time_value='12:34'" in repr_str


def test_models_module_imports():
    from app.utils.db import Base, ClockUpdate, SessionLocal, create_tables, engine, get_db

    assert Base is not None
    assert ClockUpdate is not None
    assert create_tables is not None
    assert get_db is not None
    assert SessionLocal is not None
    assert engine is not None


def test_clock_update_table_name():
    from app.utils.db import ClockUpdate

    assert ClockUpdate.__tablename__ == "clock_updates"


def test_session_local_is_callable():
    from app.utils.db import SessionLocal

    assert callable(SessionLocal)


def test_engine_has_basic_methods():
    from app.utils.db import engine

    assert hasattr(engine, "connect")
    assert hasattr(engine, "url")


def test_models_uses_config(mocker):
    mock_config = mocker.patch("app.utils.db.config")
    mock_config.DATABASE_URL = "sqlite:///test.db"
    mock_config.DEBUG = False

    import app.utils.db as models_module

    assert models_module.config == mock_config
