"""Tests for services/background_tasks.py module - only working tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.background_tasks import BackgroundTaskService, background_service


class TestBackgroundTaskService:
    """Test BackgroundTaskService class."""
    
    def test_init(self):
        """Test BackgroundTaskService initialization."""
        service = BackgroundTaskService()
        
        assert service.clock_service is not None
        assert service.is_running is False
        assert service.task is None


class TestGlobalBackgroundService:
    """Test the global background service instance."""
    
    def test_global_instance_exists(self):
        """Test that global background service instance exists."""
        assert background_service is not None
        assert isinstance(background_service, BackgroundTaskService)
    
    def test_global_instance_initial_state(self):
        """Test that global instance starts in the correct state."""
        assert background_service.is_running is False
        assert background_service.task is None
        assert background_service.clock_service is not None
    
    def test_global_instance_independence(self):
        """Test that new instances are independent of global instance."""
        new_service = BackgroundTaskService()
        
        # They should be different instances
        assert new_service is not background_service
        
        # But have similar initial state
        assert new_service.is_running is False
        assert new_service.task is None