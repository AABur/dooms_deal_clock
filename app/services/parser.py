import re
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class ClockData:
    """Структура данных часов"""
    time: str
    description: str
    raw_message: str

class MessageParser:
    """Парсер сообщений из Telegram канала"""
    
    def __init__(self):
        # Регулярные выражения для поиска времени
        self.time_patterns = [
            r'(\d{1,2}):(\d{2}):(\d{2})',  # HH:MM:SS
            r'(\d{1,2}):(\d{2})',          # HH:MM
            r'(\d{1,2})\.(\d{2})\.(\d{2})', # HH.MM.SS
            r'(\d{1,2})\.(\d{2})',          # HH.MM
        ]
        
        # Ключевые слова для определения сообщений с часами
        self.clock_keywords = [
            'час', 'время', 'минут', 'секунд', 
            'договор', 'соглашение', 'сделка',
            'судного', 'до', 'остается', 'осталось'
        ]
    
    def parse_message(self, message_text: str) -> Optional[ClockData]:
        """
        Парсит сообщение и извлекает данные часов
        
        Args:
            message_text: Текст сообщения из Telegram
            
        Returns:
            ClockData или None если не удалось распарсить
        """
        if not message_text:
            return None
            
        message_text = message_text.strip()
        
        # Проверяем, содержит ли сообщение ключевые слова
        if not self._contains_clock_keywords(message_text.lower()):
            return None
        
        # Ищем время в сообщении
        time = self._extract_time(message_text)
        if not time:
            return None
        
        # Извлекаем описание
        description = self._extract_description(message_text, time)
        
        return ClockData(
            time=time,
            description=description,
            raw_message=message_text
        )
    
    def _contains_clock_keywords(self, text: str) -> bool:
        """Проверяет наличие ключевых слов часов в тексте"""
        return any(keyword in text for keyword in self.clock_keywords)
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Извлекает время из текста"""
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # HH:MM:SS
                    return f"{int(groups[0]):02d}:{int(groups[1]):02d}:{int(groups[2]):02d}"
                elif len(groups) == 2:  # HH:MM
                    return f"{int(groups[0]):02d}:{int(groups[1]):02d}:00"
        
        return None
    
    def _extract_description(self, text: str, time_str: str) -> str:
        """Извлекает описание из текста"""
        # Убираем время из текста
        text_without_time = re.sub(r'\d{1,2}[:.]\d{2}([:.]\d{2})?', '', text).strip()
        
        # Убираем эмодзи и лишние символы
        text_without_time = re.sub(r'[🕐-🕧⏰⏱⏲🔔🎯⚡]', '', text_without_time)
        
        # Убираем множественные пробелы и переносы строк
        text_without_time = re.sub(r'\s+', ' ', text_without_time).strip()
        
        # Если описание пустое, возвращаем дефолтное
        if not text_without_time or len(text_without_time) < 10:
            return "Время до заключения эпохального соглашения"
        
        return text_without_time[:200]  # Ограничиваем длину
    
    def parse_multiple_formats(self, message_text: str) -> Dict[str, Any]:
        """
        Пробует разные форматы парсинга для отладки
        
        Returns:
            Словарь с результатами разных попыток парсинга
        """
        results = {
            'original_text': message_text,
            'has_keywords': self._contains_clock_keywords(message_text.lower()),
            'found_times': [],
            'parsed_data': None
        }
        
        # Ищем все возможные времена
        for pattern in self.time_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                results['found_times'].append({
                    'pattern': pattern,
                    'match': match,
                    'formatted': self._format_time_match(match)
                })
        
        # Пробуем стандартный парсинг
        results['parsed_data'] = self.parse_message(message_text)
        
        return results
    
    def _format_time_match(self, match_groups: tuple) -> str:
        """Форматирует найденное время"""
        if len(match_groups) == 3:
            return f"{int(match_groups[0]):02d}:{int(match_groups[1]):02d}:{int(match_groups[2]):02d}"
        elif len(match_groups) == 2:
            return f"{int(match_groups[0]):02d}:{int(match_groups[1]):02d}:00"
        return str(match_groups)