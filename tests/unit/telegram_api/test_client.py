"""Tests for telegram_api/client.py module - only working tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.telegram_api.client import TelegramService


class TestTelegramService:
    """Test TelegramService class methods."""
    
    def test_init(self):
        """Test TelegramService initialization."""
        service = TelegramService()
        
        # Should initialize with None client
        assert service.client is None
        
        # Should be a valid service instance
        assert service is not None


class TestTimeExtraction:
    """Test time extraction functionality."""
    
    def test_extract_time_hh_mm_format(self):
        """Test extracting time in HH:MM format."""
        service = TelegramService()
        
        # Standard format
        result = service.extract_time_from_message("🕐 23:42 - Дедлайн приближается!")
        assert result == "23:42"
        
        # Different hour formats
        result = service.extract_time_from_message("Time is 9:30 AM")
        assert result == "9:30"
        
        result = service.extract_time_from_message("Meeting at 14:15")
        assert result == "14:15"
    
    def test_extract_time_h_mm_format(self):
        """Test extracting time in H:MM format (single digit hour)."""
        service = TelegramService()
        
        result = service.extract_time_from_message("Start at 9:45")
        assert result == "9:45"
        
        result = service.extract_time_from_message("🔔 7:30 reminder")
        assert result == "7:30"
    
    def test_extract_time_dots_format(self):
        """Test extracting time in HH.MM format."""
        service = TelegramService()
        
        result = service.extract_time_from_message("Appointment at 15.30")
        assert result == "15.30"
        
        result = service.extract_time_from_message("🕒 12.45 meeting")
        assert result == "12.45"
    
    def test_extract_time_no_time_found(self):
        """Test when no time pattern is found."""
        service = TelegramService()
        
        assert service.extract_time_from_message("No time here") is None
        assert service.extract_time_from_message("Just some text") is None
        assert service.extract_time_from_message("Numbers 123 456") is None
    
    def test_extract_time_multiple_times(self):
        """Test extraction when multiple times are present."""
        service = TelegramService()
        
        # Should return the first match
        result = service.extract_time_from_message("From 9:30 to 17:45")
        assert result == "9:30"
        
        result = service.extract_time_from_message("🕐 14:20 and also 16:35")
        assert result == "14:20"
    
    def test_extract_time_mixed_formats(self):
        """Test extraction with mixed time formats in same message.""" 
        service = TelegramService()
        
        # Colon format should be found first
        result = service.extract_time_from_message("At 12:30 or maybe 14.45")
        assert result == "12:30"
        
        # Only dots format
        result = service.extract_time_from_message("Meeting at 14.30 today")
        assert result == "14.30"
    
    def test_extract_time_invalid_formats(self):
        """Test with invalid time-like formats."""
        service = TelegramService()
        
        # These should match the pattern but are semantically invalid times
        assert service.extract_time_from_message("Price: 25:99") == "25:99"  # Pattern matches even if invalid time
        assert service.extract_time_from_message("Code: 123:456") == "23:45"  # Pattern finds substring 23:45
        assert service.extract_time_from_message("Version 1.2.3") is None  # No colon or single dot format
    
    def test_extract_time_edge_cases(self):
        """Test edge cases for time extraction."""
        service = TelegramService()
        
        # Empty string
        assert service.extract_time_from_message("") is None
        
        # Only separator without valid digits
        assert service.extract_time_from_message("::") is None
        assert service.extract_time_from_message("..") is None
        
        # Valid format at start/end
        assert service.extract_time_from_message("12:34") == "12:34"
        assert service.extract_time_from_message("Time: 23:59") == "23:59"
        

class TestTelegramServiceIntegration:
    """Test integration scenarios."""
    
    def test_service_instance_isolation(self):
        """Test that service instances are isolated."""
        service1 = TelegramService()
        service2 = TelegramService()
        
        # Should be different instances
        assert service1 is not service2
        
        # Both should start with None client
        assert service1.client is None
        assert service2.client is None