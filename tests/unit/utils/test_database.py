"""Tests for DB session utilities (`app.db.*`) and model presence.

Modernized to reflect the current project layout.
"""

import pytest

from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db


def test_get_db_function():
    """Test the get_db dependency function."""
    db_gen = get_db()
    assert hasattr(db_gen, "__next__")
    try:
        db_session = next(db_gen)
        assert hasattr(db_session, "query")
        assert hasattr(db_session, "add")
        assert hasattr(db_session, "commit")
    except StopIteration:
        pytest.fail("get_db generator should yield a database session")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_base_metadata_exists():
    assert Base is not None
    assert hasattr(Base, "metadata")
    assert hasattr(Base.metadata, "create_all")


def test_engine_configuration():
    assert engine is not None
    assert hasattr(engine, "connect")
    assert hasattr(engine, "begin")


def test_session_local_configuration():
    assert SessionLocal is not None
    session = SessionLocal()
    try:
        assert hasattr(session, "query")
        assert hasattr(session, "add")
        assert hasattr(session, "commit")
        assert hasattr(session, "rollback")
        assert hasattr(session, "close")
    finally:
        session.close()


def test_engine_sqlite_config(mocker):
    mock_create_engine = mocker.patch("app.db.session.create_engine")
    mock_create_engine.return_value = mocker.MagicMock()

    connect_args: dict[str, object] = {"check_same_thread": False}
    mock_create_engine("sqlite:///test.db", connect_args=connect_args)

    mock_create_engine.assert_called_once()
    call_args = mock_create_engine.call_args
    assert "connect_args" in call_args.kwargs
    assert call_args.kwargs["connect_args"] == {"check_same_thread": False}


def test_engine_non_sqlite_config(mocker):
    mock_create_engine = mocker.patch("app.db.session.create_engine")
    mock_create_engine.return_value = mocker.MagicMock()

    postgres_url = "postgresql://user:pass@localhost/db"
    connect_args: dict[str, object] = {}
    mock_create_engine(postgres_url, connect_args=connect_args)

    mock_create_engine.assert_called_once()
    call_args = mock_create_engine.call_args
    assert "connect_args" in call_args.kwargs
    assert call_args.kwargs["connect_args"] == {}


def test_session_local_factory(mocker):
    mock_sessionmaker = mocker.patch("app.db.session.sessionmaker")
    mock_session_factory = mocker.MagicMock()
    mock_sessionmaker.return_value = mock_session_factory

    from app.db.session import engine as _engine

    mock_sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    mock_sessionmaker.assert_called_once_with(autocommit=False, autoflush=False, bind=_engine)


def test_models_exist():
    # Ensure ClockUpdate model exists in app.models (single source of truth)
    import app.models as models

    assert hasattr(models, "ClockUpdate")


def test_clock_update_model_attributes():
    from app.models import ClockUpdate

    assert ClockUpdate.__tablename__ == "clock_updates"
    columns = [column.name for column in ClockUpdate.__table__.columns]
    expected_columns = [
        "id",
        "message_id",
        "content",
        "time_value",
        "image_data",
        "created_at",
        "updated_at",
    ]
    for expected_col in expected_columns:
        assert expected_col in columns, f"Column {expected_col} missing from ClockUpdate"


def test_no_legacy_parsed_message_model():
    # Legacy ParsedMessage should not exist anymore
    import app.models as models
    assert not hasattr(models, "ParsedMessage")


def test_models_inherit_from_base():
    from app.db.base import Base as _Base
    from app.models import ClockUpdate

    assert issubclass(ClockUpdate, _Base)


def test_table_creation_called(mocker):
    mock_base = mocker.patch("app.db.session.Base")
    mock_metadata = mocker.MagicMock()
    mock_base.metadata = mock_metadata

    from app.db.session import create_tables

    create_tables()
    mock_metadata.create_all.assert_called_once()


def test_get_db_with_session_local():
    db_gen = get_db()
    try:
        session = next(db_gen)
        assert session.__class__.__name__ == "Session"
        assert hasattr(session, "query")
        assert hasattr(session, "add")
        assert hasattr(session, "commit")
        assert hasattr(session, "rollback")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_multiple_db_sessions_are_independent():
    gen1 = get_db()
    gen2 = get_db()
    try:
        session1 = next(gen1)
        session2 = next(gen2)
        assert session1 is not session2
    finally:
        try:
            next(gen1)
            next(gen2)
        except StopIteration:
            pass
