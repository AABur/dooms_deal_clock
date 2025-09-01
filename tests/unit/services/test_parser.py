"""Tests for the message parser module."""

import pytest

from app.services.parser import ClockData, MessageParser


@pytest.fixture
def parser():
    """Create a MessageParser instance."""
    return MessageParser()


@pytest.mark.parametrize(
    "message,expected_time,expected_in_description",
    [
        ("🕐 23:42 - Дедлайн приближается! Время до заключения соглашения.", "23:42:00", "Дедлайн приближается"),
        ("⏰ 15:30:45 до судного договора остается совсем немного времени", "15:30:45", "до судного договора остается"),
        ("🔔 12.15 - время заключения сделки приближается", "12:15:00", "время заключения сделки"),
        ("⚡ 09.25.30 секунд до договора", "09:25:30", "секунд до договора"),
    ],
)
def test_parse_message_time_patterns(parser, message, expected_time, expected_in_description):
    """Parse messages with different time formats and verify outputs."""
    # Arrange is done by parameters
    # Act
    result = parser.parse_message(message)
    # Assert
    assert result is not None
    assert result.time == expected_time
    assert expected_in_description in result.description
    assert result.raw_message == message


@pytest.mark.parametrize(
    "message",
    [
        "This is just a regular message with 12:30 but no relevant keywords",
    ],
)
def test_parse_message_no_keywords(parser, message):
    """Messages without keywords should not parse to ClockData."""
    assert parser.parse_message(message) is None


@pytest.mark.parametrize(
    "message",
    [
        "Время договора судного приближается но никто не знает когда",
    ],
)
def test_parse_message_no_time(parser, message):
    """Messages with keywords but without time should not parse."""
    assert parser.parse_message(message) is None


@pytest.mark.parametrize("message", ["", None, "   "])
def test_parse_message_empty_text(parser, message):
    """Empty or whitespace messages should return None."""
    assert parser.parse_message(message) is None


def test_parse_message_multiple_times(parser):
    """Test parsing message with multiple time formats."""
    message = "🕐 23:42 и также 15.30.45 - два времени для договора"

    result = parser.parse_message(message)

    assert result is not None
    # Should extract the first found time
    assert result.time == "23:42:00"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("время до договора", True),
        ("часы судного дня", True),
        ("минуты до сделки", True),
        ("секунды остается", True),
        ("договор соглашения", True),  # "соглашение" is a keyword
        ("просто обычное сообщение", False),
        ("", False),
        ("время", True),  # Single keyword should match
        ("ВРЕМЯ ДОГОВОР", True),  # Case insensitive
    ],
)
def test_contains_clock_keywords(parser, text, expected):
    assert parser._contains_clock_keywords(text.lower()) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Current time is 14:25", "14:25:00"),
        ("Time: 09:05:30", "09:05:30"),
        ("Time is 7:45", "07:45:00"),
        ("Format 23.59", "23:59:00"),
        ("Format 12.34.56", "12:34:56"),
        ("No time here", None),
        ("Invalid 25:70", "25:70:00"),
        ("", None),
    ],
)
def test_extract_time_various_formats(parser, text, expected):
    assert parser._extract_time(text) == expected


@pytest.mark.parametrize(
    "message,expected_part",
    [
        ("🕐 23:42 - Дедлайн приближается!", "- Дедлайн приближается!"),
        ("⏰ 15:30 время договора настало", "время договора настало"),
        ("12.30 - сделка судного дня", "- сделка судного дня"),
        ("🔔 09:15:30 секунды до соглашения", "секунды до соглашения"),
    ],
)
def test_extract_description_removes_time(parser, message, expected_part):
    result = parser._extract_description(message, "doesn't matter")
    assert expected_part in result
    # Should not contain a time pattern
    assert not any(ch.isdigit() and ":" in result for ch in result)


@pytest.mark.parametrize(
    "message,expected",
    [
        ("🕐 23:42", "Время до заключения эпохального соглашения"),
        ("⏰ 15:30   ", "Время до заключения эпохального соглашения"),
        ("12:30 - short", "Время до заключения эпохального соглашения"),
    ],
)
def test_extract_description_default_fallback(parser, message, expected):
    assert parser._extract_description(message, "12:30") == expected


def test_extract_description_length_limit(parser):
    """Test description length limitation."""
    long_message = "🕐 12:30 " + "очень длинное описание " * 20
    result = parser._extract_description(long_message, "12:30")

    assert len(result) <= 200


def test_parse_multiple_formats_debug(parser):
    """Test debug parsing method."""
    message = "🕐 23:42 и 15.30.45 - время договора"

    result = parser.parse_multiple_formats(message)

    assert result["original_text"] == message
    assert result["has_keywords"] is True
    assert len(result["found_times"]) >= 1  # Should find at least one time
    assert result["parsed_data"] is not None
    assert result["parsed_data"].time == "23:42:00"  # First match


def test_parse_multiple_formats_no_matches(parser):
    """Test debug parsing with no matches."""
    message = "Regular message without any time or keywords"

    result = parser.parse_multiple_formats(message)

    assert result["original_text"] == message
    assert result["has_keywords"] is False
    assert len(result["found_times"]) == 0
    assert result["parsed_data"] is None


def test_format_time_match(parser):
    """Test time formatting from regex matches."""
    # Test 2-group match (HH:MM)
    result = parser._format_time_match(("15", "30"))
    assert result == "15:30:00"

    # Test 3-group match (HH:MM:SS)
    result = parser._format_time_match(("09", "25", "45"))
    assert result == "09:25:45"

    # Test single digit formatting
    result = parser._format_time_match(("5", "7"))
    assert result == "05:07:00"

    # Test unexpected number of groups (fallback case)
    result = parser._format_time_match(("23",))
    assert result == "('23',)"


def test_clock_data_structure():
    """Test ClockData dataclass structure."""
    data = ClockData(time="12:30:00", description="Test description", raw_message="Original message")

    assert data.time == "12:30:00"
    assert data.description == "Test description"
    assert data.raw_message == "Original message"


def test_parser_keyword_patterns(parser):
    """Test that parser recognizes all expected keywords."""
    expected_keywords = [
        "час",
        "время",
        "минут",
        "секунд",
        "договор",
        "соглашение",
        "сделка",
        "судного",
        "до",
        "остается",
        "осталось",
    ]

    assert set(parser.clock_keywords) == set(expected_keywords)


def test_parser_time_patterns(parser):
    """Test that parser has expected time patterns."""
    expected_patterns = [
        r"(\d{1,2}):(\d{2}):(\d{2})",  # HH:MM:SS
        r"(\d{1,2}):(\d{2})",  # HH:MM
        r"(\d{1,2})\.(\d{2})\.(\d{2})",  # HH.MM.SS
        r"(\d{1,2})\.(\d{2})",  # HH.MM
    ]

    assert parser.time_patterns == expected_patterns
