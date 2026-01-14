"""
Модуль для управления контекстом пользователей
Хранит историю пересланных сообщений для каждого пользователя
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass

import config

logger = logging.getLogger(__name__)


@dataclass
class ContextMessage:
    """Структура для хранения сообщения в контексте"""
    text: str
    timestamp: datetime
    message_id: Optional[int] = None


class ContextManager:
    """Менеджер контекста для хранения истории сообщений пользователей"""
    
    def __init__(self):
        # Словарь: user_id -> список сообщений
        self.user_contexts: Dict[int, List[ContextMessage]] = {}
        # Словарь: user_id -> время последнего сообщения
        self.user_last_activity: Dict[int, datetime] = {}
    
    def add_message(self, user_id: int, text: str, message_id: Optional[int] = None) -> None:
        """
        Добавляет сообщение в контекст пользователя
        
        Args:
            user_id: ID пользователя
            text: Текст сообщения
            message_id: ID сообщения (опционально)
        """
        if not text or len(text.strip()) < 5:
            logger.debug(f"Сообщение от пользователя {user_id} слишком короткое, пропускаем")
            return
        
        # Инициализируем контекст, если его нет
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = []
        
        # Создаем новое сообщение
        message = ContextMessage(
            text=text.strip(),
            timestamp=datetime.now(),
            message_id=message_id
        )
        
        # Добавляем сообщение
        self.user_contexts[user_id].append(message)
        self.user_last_activity[user_id] = datetime.now()
        
        # Ограничиваем количество сообщений
        if len(self.user_contexts[user_id]) > config.CONTEXT_MAX_MESSAGES:
            self.user_contexts[user_id] = self.user_contexts[user_id][-config.CONTEXT_MAX_MESSAGES:]
            logger.debug(f"Контекст пользователя {user_id} обрезан до {config.CONTEXT_MAX_MESSAGES} сообщений")
        
        logger.info(f"Добавлено сообщение в контекст пользователя {user_id}. Всего сообщений: {len(self.user_contexts[user_id])}")
    
    def get_context_text(self, user_id: int) -> Optional[str]:
        """
        Получает объединенный текст контекста пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Объединенный текст контекста или None, если контекст пуст
        """
        if user_id not in self.user_contexts or not self.user_contexts[user_id]:
            return None
        
        # Проверяем таймаут
        if self._is_context_expired(user_id):
            logger.info(f"Контекст пользователя {user_id} истек, очищаем")
            self.clear_context(user_id)
            return None
        
        # Объединяем сообщения с временными метками
        context_parts = []
        for i, msg in enumerate(self.user_contexts[user_id], 1):
            time_str = msg.timestamp.strftime("%H:%M:%S")
            context_parts.append(f"[Сообщение {i}, {time_str}]\n{msg.text}")
        
        context_text = "\n\n---\n\n".join(context_parts)
        
        # Проверяем длину (примерная оценка токенов: 1 токен ≈ 4 символа)
        estimated_tokens = len(context_text) // 4
        if estimated_tokens > config.CONTEXT_MAX_TOKENS:
            logger.warning(f"Контекст пользователя {user_id} слишком длинный ({estimated_tokens} токенов), обрезаем")
            # Берем последние сообщения, которые помещаются в лимит
            context_text = self._truncate_context(user_id, config.CONTEXT_MAX_TOKENS)
        
        return context_text
    
    def _truncate_context(self, user_id: int, max_tokens: int) -> str:
        """
        Обрезает контекст до максимального количества токенов
        
        Args:
            user_id: ID пользователя
            max_tokens: Максимальное количество токенов
            
        Returns:
            Обрезанный текст контекста
        """
        messages = self.user_contexts[user_id]
        max_chars = max_tokens * 4  # Примерная оценка
        
        # Пробуем взять последние N сообщений
        for i in range(len(messages), 0, -1):
            context_parts = []
            for msg in messages[-i:]:
                time_str = msg.timestamp.strftime("%H:%M:%S")
                context_parts.append(f"[Сообщение {len(messages) - i + messages[-i:].index(msg) + 1}, {time_str}]\n{msg.text}")
            
            context_text = "\n\n---\n\n".join(context_parts)
            if len(context_text) <= max_chars:
                return context_text
        
        # Если даже одно сообщение не помещается, берем его часть
        if messages:
            last_msg = messages[-1]
            return last_msg.text[:max_chars]
        
        return ""
    
    def clear_context(self, user_id: int) -> None:
        """
        Очищает контекст пользователя
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
        if user_id in self.user_last_activity:
            del self.user_last_activity[user_id]
        logger.info(f"Контекст пользователя {user_id} очищен")
    
    def has_context(self, user_id: int) -> bool:
        """
        Проверяет, есть ли у пользователя контекст
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если есть контекст, False иначе
        """
        if user_id not in self.user_contexts or not self.user_contexts[user_id]:
            return False
        
        # Проверяем таймаут
        if self._is_context_expired(user_id):
            self.clear_context(user_id)
            return False
        
        return True
    
    def get_message_count(self, user_id: int) -> int:
        """
        Возвращает количество сообщений в контексте пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество сообщений
        """
        if not self.has_context(user_id):
            return 0
        return len(self.user_contexts[user_id])
    
    def _is_context_expired(self, user_id: int) -> bool:
        """
        Проверяет, истек ли таймаут контекста
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если контекст истек, False иначе
        """
        if user_id not in self.user_last_activity:
            return True
        
        timeout = timedelta(minutes=config.CONTEXT_TIMEOUT_MINUTES)
        return datetime.now() - self.user_last_activity[user_id] > timeout
    
    def cleanup_expired_contexts(self) -> None:
        """Очищает все истекшие контексты"""
        expired_users = [
            user_id for user_id in self.user_contexts.keys()
            if self._is_context_expired(user_id)
        ]
        
        for user_id in expired_users:
            self.clear_context(user_id)
        
        if expired_users:
            logger.info(f"Очищено {len(expired_users)} истекших контекстов")


# Глобальный экземпляр менеджера контекста
context_manager = ContextManager()

