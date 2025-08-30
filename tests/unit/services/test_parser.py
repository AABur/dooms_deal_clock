"""Tests for the message parser module."""

import pytest

from app.services.parser import MessageParser, ClockData


@pytest.fixture
def parser():
    """Create a MessageParser instance."""
    return MessageParser()


def test_parse_message_with_time_hhmm(parser):
    """Test parsing message with HH:MM format."""
    message = "🕐 23:42 - Дедлайн приближается! Время до заключения соглашения."
    
    result = parser.parse_message(message)
    
    assert result is not None
    assert result.time == "23:42:00"
    assert "Дедлайн приближается" in result.description
    assert result.raw_message == message


def test_parse_message_with_time_hhmmss(parser):
    """Test parsing message with HH:MM:SS format."""
    message = "⏰ 15:30:45 до судного договора остается совсем немного времени"
    
    result = parser.parse_message(message)
    
    assert result is not None
    assert result.time == "15:30:45"
    assert "до судного договора остается" in result.description


def test_parse_message_with_dots_format(parser):
    """Test parsing message with dots format (HH.MM)."""
    message = "🔔 12.15 - время заключения сделки приближается"
    
    result = parser.parse_message(message)
    
    assert result is not None
    assert result.time == "12:15:00"
    assert "время заключения сделки" in result.description


def test_parse_message_with_dots_and_seconds(parser):
    """Test parsing message with dots format (HH.MM.SS)."""
    message = "⚡ 09.25.30 секунд до договора"
    
    result = parser.parse_message(message)
    
    assert result is not None
    assert result.time == "09:25:30"
    assert "секунд до договора" in result.description


def test_parse_message_no_keywords(parser):
    """Test parsing message without clock keywords."""
    message = "This is just a regular message with 12:30 but no relevant keywords"
    
    result = parser.parse_message(message)
    
    assert result is None


def test_parse_message_no_time(parser):
    """Test parsing message with keywords but no time."""
    message = "Время договора судного приближается но никто не знает когда"
    
    result = parser.parse_message(message)
    
    assert result is None


def test_parse_message_empty_text(parser):
    """Test parsing empty message."""
    result = parser.parse_message("")
    assert result is None
    
    result = parser.parse_message(None)
    assert result is None
    
    result = parser.parse_message("   ")
    assert result is None


def test_parse_message_multiple_times(parser):
    """Test parsing message with multiple time formats."""
    message = "🕐 23:42 и также 15.30.45 - два времени для договора"
    
    result = parser.parse_message(message)
    
    assert result is not None
    # Should extract the first found time
    assert result.time == "23:42:00"


def test_contains_clock_keywords(parser):
    """Test keyword detection."""
    test_cases = [
        ("время до договора", True),
        ("часы судного дня", True),
        ("минуты до сделки", True),
        ("секунды остается", True),
        ("договор соглашения", True),  # "соглашение" is a keyword
        ("просто обычное сообщение", False),
        ("", False),
        ("время", True),  # Single keyword should match
        ("ВРЕМЯ ДОГОВОР", True),  # Case insensitive
    ]
    
    for text, expected in test_cases:
        result = parser._contains_clock_keywords(text.lower())
        assert result == expected, f"Failed for text: '{text}'"


def test_extract_time_various_formats(parser):
    """Test time extraction with various formats."""
    test_cases = [
        ("Current time is 14:25", "14:25:00"),
        ("Time: 09:05:30", "09:05:30"),
        ("Time is 7:45", "07:45:00"),
        ("Format 23.59", "23:59:00"),
        ("Format 12.34.56", "12:34:56"),
        ("No time here", None),
        ("Invalid 25:70", "25:70:00"),  # Parser doesn't validate, just formats
        ("", None),
    ]
    
    for text, expected in test_cases:
        result = parser._extract_time(text)
        assert result == expected, f"Failed for text: '{text}'"


def test_extract_description_removes_time(parser):
    """Test description extraction removes time and formats properly."""
    test_cases = [
        ("🕐 23:42 - Дедлайн приближается!", "- Дедлайн приближается!"),
        ("⏰ 15:30 время договора настало", "время договора настало"),
        ("12.30 - сделка судного дня", "- сделка судного дня"),
        ("🔔 09:15:30 секунды до соглашения", "секунды до соглашения"),
    ]
    
    for message, expected_part in test_cases:
        result = parser._extract_description(message, "doesn't matter")
        assert expected_part in result
        # Should not contain time pattern
        assert not any(char.isdigit() and ":" in result for char in result)


def test_extract_description_default_fallback(parser):
    """Test description fallback for short or empty descriptions."""
    test_cases = [
        ("🕐 23:42", "Время до заключения эпохального соглашения"),
        ("⏰ 15:30   ", "Время до заключения эпохального соглашения"),
        ("12:30 - short", "Время до заключения эпохального соглашения"),
    ]
    
    for message, expected in test_cases:
        result = parser._extract_description(message, "12:30")
        assert result == expected


def test_extract_description_length_limit(parser):
    """Test description length limitation."""
    long_message = "🕐 12:30 " + "очень длинное описание " * 20
    result = parser._extract_description(long_message, "12:30")
    
    assert len(result) <= 200


def test_parse_multiple_formats_debug(parser):
    """Test debug parsing method."""
    message = "🕐 23:42 и 15.30.45 - время договора"
    
    result = parser.parse_multiple_formats(message)
    
    assert result['original_text'] == message
    assert result['has_keywords'] is True
    assert len(result['found_times']) >= 1  # Should find at least one time
    assert result['parsed_data'] is not None
    assert result['parsed_data'].time == "23:42:00"  # First match


def test_parse_multiple_formats_no_matches(parser):
    """Test debug parsing with no matches."""
    message = "Regular message without any time or keywords"
    
    result = parser.parse_multiple_formats(message)
    
    assert result['original_text'] == message
    assert result['has_keywords'] is False
    assert len(result['found_times']) == 0
    assert result['parsed_data'] is None


def test_format_time_match(parser):
    """Test time formatting from regex matches."""
    # Test 2-group match (HH:MM)
    result = parser._format_time_match(('15', '30'))
    assert result == "15:30:00"
    
    # Test 3-group match (HH:MM:SS)
    result = parser._format_time_match(('09', '25', '45'))
    assert result == "09:25:45"
    
    # Test single digit formatting
    result = parser._format_time_match(('5', '7'))
    assert result == "05:07:00"
    
    # Test unexpected number of groups (fallback case)
    result = parser._format_time_match(('23',))
    assert result == "('23',)"


def test_clock_data_structure():
    """Test ClockData dataclass structure."""
    data = ClockData(
        time="12:30:00",
        description="Test description",
        raw_message="Original message"
    )
    
    assert data.time == "12:30:00"
    assert data.description == "Test description"
    assert data.raw_message == "Original message"


def test_parser_keyword_patterns(parser):
    """Test that parser recognizes all expected keywords."""
    expected_keywords = [
        'час', 'время', 'минут', 'секунд', 
        'договор', 'соглашение', 'сделка',
        'судного', 'до', 'остается', 'осталось'
    ]
    
    assert set(parser.clock_keywords) == set(expected_keywords)


def test_parser_time_patterns(parser):
    """Test that parser has expected time patterns."""
    expected_patterns = [
        r'(\d{1,2}):(\d{2}):(\d{2})',  # HH:MM:SS
        r'(\d{1,2}):(\d{2})',          # HH:MM
        r'(\d{1,2})\.(\d{2})\.(\d{2})', # HH.MM.SS
        r'(\d{1,2})\.(\d{2})',          # HH.MM
    ]
    
    assert parser.time_patterns == expected_patterns