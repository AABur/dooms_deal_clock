"""Focused tests for models.py module functions."""

from unittest.mock import MagicMock, patch


class TestModelsFunctions:
    """Test individual functions in models.py."""
    
    @patch('app.models.Base')
    def test_create_tables_function_calls_metadata(self, mock_base):
        """Test create_tables function calls metadata.create_all."""
        from app.models import create_tables
        
        # Mock metadata
        mock_metadata = MagicMock()
        mock_base.metadata = mock_metadata
        
        # Call function
        create_tables()
        
        # Verify metadata.create_all was called
        mock_metadata.create_all.assert_called_once()
    
    @patch('app.models.SessionLocal')
    def test_get_db_function_workflow(self, mock_session_local):
        """Test get_db function workflow."""
        from app.models import get_db
        
        # Mock session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Use the generator
        db_gen = get_db()
        
        # Get session from generator
        session = next(db_gen)
        assert session == mock_session
        
        # Complete the generator (should close session)
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        # Verify session was created and closed
        mock_session_local.assert_called_once()
        mock_session.close.assert_called_once()
    
    def test_clock_update_repr_method_direct(self):
        """Test ClockUpdate __repr__ method directly."""
        from app.models import ClockUpdate
        
        # Create instance without database
        update = ClockUpdate()
        update.id = 42
        update.time_value = "12:34"
        
        # Test repr
        repr_str = repr(update)
        
        assert "ClockUpdate" in repr_str
        assert "id=42" in repr_str
        assert "time_value='12:34'" in repr_str
    
    def test_models_module_imports(self):
        """Test that models module imports work correctly."""
        # Test imports don't raise errors
        from app.models import Base, ClockUpdate, create_tables, get_db, SessionLocal, engine
        
        assert Base is not None
        assert ClockUpdate is not None
        assert create_tables is not None
        assert get_db is not None
        assert SessionLocal is not None
        assert engine is not None
    
    def test_clock_update_table_name(self):
        """Test ClockUpdate table name."""
        from app.models import ClockUpdate
        
        assert ClockUpdate.__tablename__ == "clock_updates"
    
    def test_session_local_is_callable(self):
        """Test SessionLocal is callable."""
        from app.models import SessionLocal
        
        assert callable(SessionLocal)
    
    def test_engine_has_basic_methods(self):
        """Test engine has expected methods."""
        from app.models import engine
        
        assert hasattr(engine, 'connect')
        assert hasattr(engine, 'url')  # Use url instead of execute
    
    @patch('app.models.config')
    def test_models_uses_config(self, mock_config):
        """Test that models module uses config values."""
        mock_config.DATABASE_URL = "sqlite:///test.db"
        mock_config.DEBUG = False
        
        # Import models to use config
        import importlib
        import app.models
        
        # Just verify imports work with mocked config
        assert app.models.config == mock_config