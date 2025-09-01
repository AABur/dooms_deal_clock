import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ClockData:
    """Data structure for clock updates.

    Attributes:
        time: Parsed time in HH:MM:SS format
        description: Description extracted from message
        raw_message: Original Telegram message text
    """

    time: str
    description: str
    raw_message: str


class MessageParser:
    """Parser for extracting clock data from Telegram channel messages."""

    def __init__(self) -> None:
        """Initialize the message parser with regex patterns and keywords."""
        self.time_patterns = [
            r"(\d{1,2}):(\d{2}):(\d{2})",  # HH:MM:SS
            r"(\d{1,2}):(\d{2})",  # HH:MM
            r"(\d{1,2})\.(\d{2})\.(\d{2})",  # HH.MM.SS
            r"(\d{1,2})\.(\d{2})",  # HH.MM
        ]

        self.clock_keywords = [
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

    def parse_message(self, message_text: str) -> Optional[ClockData]:
        """Parse message and extract clock data.

        Args:
            message_text: Text message from Telegram

        Returns:
            ClockData instance if parsing successful, None otherwise
        """
        if not message_text:
            return None

        message_text = message_text.strip()

        if not self._contains_clock_keywords(message_text.lower()):
            return None

        time = self._extract_time(message_text)
        if not time:
            return None

        description = self._extract_description(message_text, time)

        return ClockData(time=time, description=description, raw_message=message_text)

    def _contains_clock_keywords(self, text: str) -> bool:
        """Check if text contains clock-related keywords.

        Args:
            text: Text to check for keywords

        Returns:
            True if clock keywords are found, False otherwise
        """
        return any(keyword in text for keyword in self.clock_keywords)

    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from message text using regex patterns.

        Args:
            text: Message text to extract time from

        Returns:
            Formatted time string in HH:MM:SS format, or None if not found
        """
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    return f"{int(groups[0]):02d}:{int(groups[1]):02d}:{int(groups[2]):02d}"
                elif len(groups) == 2:
                    return f"{int(groups[0]):02d}:{int(groups[1]):02d}:00"

        return None

    def _extract_description(self, text: str, time_str: str) -> str:
        """Extract description from message text by removing time and cleaning up.

        Args:
            text: Original message text
            time_str: Extracted time string

        Returns:
            Cleaned description text with default fallback
        """
        text_without_time = re.sub(r"\d{1,2}[:.]\d{2}([:.]\d{2})?", "", text).strip()

        text_without_time = re.sub(r"[🕐-🕧⏰⏱⏲🔔🎯⚡]", "", text_without_time)

        text_without_time = re.sub(r"\s+", " ", text_without_time).strip()

        if not text_without_time or len(text_without_time) < 10:
            return "Время до заключения эпохального соглашения"

        return text_without_time[:200]

    def parse_multiple_formats(self, message_text: str) -> Dict[str, Any]:
        """Parse message with multiple formats for debugging purposes.

        Args:
            message_text: Message text to parse

        Returns:
            Dict with parsing results from different attempts
        """
        found_times: list[dict[str, Any]] = []
        results: dict[str, Any] = {
            "original_text": message_text,
            "has_keywords": self._contains_clock_keywords(message_text.lower()),
            "found_times": found_times,
            "parsed_data": None,
        }

        for pattern in self.time_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                found_times.append({
                    "pattern": pattern,
                    "match": match,
                    "formatted": self._format_time_match(match),
                })

        results["parsed_data"] = self.parse_message(message_text)

        return results

    def _format_time_match(self, match_groups: tuple[str, ...]) -> str:
        """Format found time matches into consistent format.

        Args:
            match_groups: Tuple of regex match groups

        Returns:
            Formatted time string
        """
        if len(match_groups) == 3:
            return f"{int(match_groups[0]):02d}:{int(match_groups[1]):02d}:{int(match_groups[2]):02d}"
        elif len(match_groups) == 2:
            return f"{int(match_groups[0]):02d}:{int(match_groups[1]):02d}:00"
        return str(match_groups)
