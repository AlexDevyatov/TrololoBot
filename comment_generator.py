"""
Модуль для генерации саркастичных комментариев на основе пересланных сообщений
Использует DeepSeek API для генерации комментариев
"""
import re
import random
import logging
from typing import Optional

from deepseek_client import (
    generate_sarcastic_comment_via_deepseek,
    generate_detailed_sarcastic_comment_via_deepseek
)

logger = logging.getLogger(__name__)


class SarcasticCommentGenerator:
    """Генератор саркастичных комментариев"""
    
    def __init__(self):
        # Шаблоны для различных типов сообщений
        self.templates = {
            'factual_claim': [
                "Интересная интерпретация фактов, особенно учитывая, что {context}",
                "Версия событий, безусловно, оригинальная. Жаль только, что реальность придерживается другого мнения",
                "Факты, безусловно, впечатляют. Если, конечно, считать фактами {claim}",
            ],
            'exaggeration': [
                "Логика железная, если игнорировать несколько ключевых деталей",
                "Преувеличение? Нет, что вы! Это просто альтернативная математика",
                "Цифры говорят сами за себя, но почему-то не в ту сторону",
                "Масштаб впечатляет, особенно если использовать специальную систему измерений",
            ],
            'contradiction': [
                "Любопытное сочетание утверждений. Особенно интересно, как они друг другу противоречат",
                "Две мысли одновременно - это всегда интересно. Особенно когда они взаимоисключающие",
                "Логическая последовательность на высоте, если читать предложения в обратном порядке",
            ],
            'general': [
                "Точка зрения, безусловно, имеет право на существование. Как и любая другая",
                "Интересный подход к интерпретации реальности",
                "Версия событий оригинальна, хотя и не совсем соответствует общепринятым представлениям",
                "Логика своеобразная, но кто я такой, чтобы спорить с альтернативной математикой",
                "Утверждение смелое, особенно если учесть, что {context}",
            ],
        }
        
        # Ключевые слова для определения типа сообщения
        self.exaggeration_keywords = [
            'все', 'никогда', 'всегда', 'абсолютно', 'полностью', 'совершенно',
            'миллионы', 'тысячи', 'всеобщий', 'тотальный', 'катастрофа'
        ]
        
        self.contradiction_keywords = [
            'но', 'однако', 'хотя', 'несмотря на', 'в то же время', 'с другой стороны'
        ]
    
    def _detect_message_type(self, text: str) -> str:
        """Определяет тип сообщения для выбора подходящего шаблона"""
        text_lower = text.lower()
        
        # Проверка на преувеличения
        exaggeration_count = sum(1 for word in self.exaggeration_keywords if word in text_lower)
        if exaggeration_count >= 2:
            return 'exaggeration'
        
        # Проверка на противоречия
        contradiction_count = sum(1 for word in self.contradiction_keywords if word in text_lower)
        if contradiction_count >= 2:
            return 'contradiction'
        
        # Проверка на фактические утверждения (наличие цифр, дат, конкретных данных)
        if re.search(r'\d+', text):
            return 'factual_claim'
        
        return 'general'
    
    def _extract_context(self, text: str) -> Optional[str]:
        """Извлекает ключевой контекст из текста для использования в шаблонах"""
        # Ищем числа
        numbers = re.findall(r'\d+', text)
        if numbers:
            return f"цифры говорят о другом"
        
        # Ищем утверждения с преувеличениями
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if any(word in sentence.lower() for word in self.exaggeration_keywords):
                # Упрощаем предложение
                words = sentence.split()[:5]
                return ' '.join(words) + '...'
        
        return None
    
    def generate_sarcastic_comment(self, text: str) -> str:
        """
        Генерирует саркастичный комментарий на основе текста пересланного сообщения
        
        Args:
            text: Текст пересланного сообщения
            
        Returns:
            Саркастичный комментарий
        """
        if not text or len(text.strip()) < 10:
            return "Сообщение слишком короткое для глубокого анализа. Но идея интересная."
        
        # Определяем тип сообщения
        message_type = self._detect_message_type(text)
        
        # Извлекаем контекст
        context = self._extract_context(text)
        
        # Выбираем подходящий шаблон
        templates = self.templates.get(message_type, self.templates['general'])
        template = random.choice(templates)
        
        # Заполняем шаблон
        if '{context}' in template:
            if context:
                comment = template.format(context=context)
            else:
                # Если контекст не найден, используем общий шаблон
                comment = random.choice(self.templates['general'])
        else:
            comment = template
        
        return comment


def generate_sarcastic_comment(text: str) -> str:
    """
    Генерирует саркастичный комментарий через DeepSeek API
    В случае ошибки API использует локальную генерацию как fallback
    
    Args:
        text: Текст пересланного сообщения
        
    Returns:
        Саркастичный комментарий
    """
    # Пытаемся использовать DeepSeek API
    try:
        comment = generate_sarcastic_comment_via_deepseek(text)
        if comment:
            return comment
        else:
            logger.warning("DeepSeek API вернул None, используем локальную генерацию")
    except Exception as e:
        logger.error(f"Ошибка при обращении к DeepSeek API: {e}, используем локальную генерацию")
    
    # Fallback на локальную генерацию
    generator = SarcasticCommentGenerator()
    return generator.generate_sarcastic_comment(text)


def generate_detailed_sarcastic_comment(context_text: str) -> str:
    """
    Генерирует развернутый саркастичный комментарий через DeepSeek API на основе контекста
    В случае ошибки API использует локальную генерацию как fallback
    
    Args:
        context_text: Текст контекста из нескольких сообщений
        
    Returns:
        Развернутый саркастичный комментарий (3-5 предложений)
    """
    # Пытаемся использовать DeepSeek API
    try:
        comment = generate_detailed_sarcastic_comment_via_deepseek(context_text)
        if comment:
            return comment
        else:
            logger.warning("DeepSeek API вернул None для развернутого комментария, используем локальную генерацию")
    except Exception as e:
        logger.error(f"Ошибка при обращении к DeepSeek API для развернутого комментария: {e}, используем локальную генерацию")
    
    # Fallback на локальную генерацию (расширенную версию)
    generator = SarcasticCommentGenerator()
    # Для развернутого комментария объединяем несколько шаблонов
    base_comment = generator.generate_sarcastic_comment(context_text)
    
    # Добавляем дополнительные предложения для развернутого ответа
    additional_phrases = [
        "Особенно интересно, как эти утверждения соотносятся друг с другом.",
        "Логическая цепочка, безусловно, оригинальна.",
        "Цифры и факты складываются в интересную картину.",
        "Версия событий имеет право на существование, как и любая другая.",
    ]
    
    # Выбираем 1-2 дополнительные фразы
    selected_phrases = random.sample(additional_phrases, min(2, len(additional_phrases)))
    detailed_comment = base_comment + " " + " ".join(selected_phrases)
    
    return detailed_comment

