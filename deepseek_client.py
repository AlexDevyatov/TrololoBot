"""
Клиент для работы с DeepSeek API
"""
import logging
import requests
from typing import Optional
import time

import config

logger = logging.getLogger(__name__)


# Константы для промптов
SYSTEM_PROMPT_SHORT = """Ты саркастичный комментатор, который анализирует пересланные сообщения.

Твоя задача - генерировать саркастичные комментарии на основе содержания сообщения.

ПРАВИЛА:
1. Анализируй факты из сообщения (текст, контекст, данные)
2. Фокусируйся на разборе логических несоответствий, преувеличений, противоречий
3. Используй иронию, гиперболу, преуменьшение для высмеивания содержания сообщения
4. Комментарий должен быть кратким (до 200 символов)
5. Разрешены умеренные оскорбления и оценки личности автора, но в меру - не переходи на откровенную грубость
6. Можно использовать легкую иронию в адрес автора, но избегай крайностей и личных нападок

Примеры стиля комментариев:
- "Интересная интерпретация фактов, особенно учитывая, что..."
- "Версия событий, безусловно, оригинальная. Жаль только, что реальность придерживается другого мнения"
- "Логика железная, если игнорировать несколько ключевых деталей"
- "Цифры говорят сами за себя, но почему-то не в ту сторону"
- "Преувеличение? Нет, что вы! Это просто альтернативная математика"
- "Автор явно не дружит с логикой, но зато с фантазией - на отлично"
- "Интересный подход к фактам - игнорировать их полностью"

Сгенерируй саркастичный комментарий на следующее сообщение:"""


SYSTEM_PROMPT_DETAILED = """Проанализируй предоставленный контекст из нескольких сообщений и сгенерируй развернутый саркастичный комментарий (3-5 предложений).

Фокус на:
1. Выявлении логических несоответствий между сообщениями
2. Обнаружении преувеличений и противоречий
3. Разборе фактов с умеренной оценкой личности автора (в меру)
4. Использовании иронии, гиперболы, сарказма
5. Структурированном ответе с анализом ключевых моментов

Разрешено:
- Умеренные оскорбления и оценки личности автора, но в разумных пределах
- Легкая ирония и сарказм в адрес автора
- Критика логики и подхода автора к фактам

Избегай:
- Откровенной грубости и крайних личных нападок
- Поверхностных односложных ответов
- Чрезмерной агрессии

Пример стиля:
'Интересно наблюдать, как факты в первом сообщении мирно сосуществуют с их полным отрицанием во втором. Автор явно не дружит с логикой, но зато с фантазией - на отлично. Особенно впечатляет утверждение о [конкретный факт], которое, судя по [противоречие], существует в параллельной реальности. Логическая цепочка, ведущая от [утверждение А] к [выводу Б], безусловно, оригинальна, если игнорировать [ключевое противоречие]. Цифры, конечно, говорят сами за себя, но почему-то складываются в совершенно иную картину, чем заявлено.'

ВАЖНО:
- Анализируй факты из сообщений (текст, контекст, данные)
- Можешь использовать умеренные оценки личности автора, но в меру
- Комментарий должен быть развернутым (3-5 предложений)
- Анализируй все сообщения в контексте как единое целое
- Сохраняй баланс между сарказмом и умеренной критикой

Проанализируй следующий контекст:"""


class DeepSeekClient:
    """Клиент для взаимодействия с DeepSeek API"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
        self.model = config.DEEPSEEK_MODEL
        self.timeout = config.DEEPSEEK_TIMEOUT
        self.max_tokens = config.DEEPSEEK_MAX_TOKENS
        self.temperature = config.DEEPSEEK_TEMPERATURE
        
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY не установлен!")
    
    def _create_prompt(self, text: str) -> str:
        """
        Создает промпт для DeepSeek с инструкциями по генерации саркастичных комментариев
        
        Args:
            text: Текст пересланного сообщения
            
        Returns:
            Промпт для отправки в API
        """
        return f"{SYSTEM_PROMPT_SHORT}\n\n{text}"
    
    def _create_detailed_prompt(self, context_text: str) -> str:
        """
        Создает промпт для DeepSeek с инструкциями по генерации развернутых саркастичных комментариев
        
        Args:
            context_text: Текст контекста из нескольких сообщений
            
        Returns:
            Промпт для отправки в API
        """
        return f"{SYSTEM_PROMPT_DETAILED}\n\n{context_text}"
    
    def generate_comment(self, text: str, retries: int = 2) -> Optional[str]:
        """
        Генерирует саркастичный комментарий через DeepSeek API
        
        Args:
            text: Текст пересланного сообщения
            retries: Количество попыток при ошибке
            
        Returns:
            Сгенерированный комментарий или None в случае ошибки
        """
        if not self.api_key:
            logger.error("DEEPSEEK_API_KEY не установлен")
            return None
        
        if not text or len(text.strip()) < 10:
            logger.warning("Текст слишком короткий для анализа")
            return None
        
        prompt = self._create_prompt(text)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"Отправка запроса к DeepSeek API (попытка {attempt + 1})")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    comment = result['choices'][0]['message']['content'].strip()
                    logger.info(f"Успешно получен комментарий от DeepSeek: {comment[:50]}...")
                    return comment
                
                elif response.status_code == 429:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded. Status: {response.status_code}")
                    if attempt < retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.info(f"Ожидание {wait_time} секунд перед повтором...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                elif response.status_code == 401:
                    logger.error("Неверный API ключ DeepSeek")
                    return None
                
                elif response.status_code >= 500:
                    # Server error
                    logger.warning(f"Ошибка сервера DeepSeek: {response.status_code}")
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.info(f"Ожидание {wait_time} секунд перед повтором...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                else:
                    logger.error(f"Неожиданный статус ответа: {response.status_code}, {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Таймаут при запросе к DeepSeek API (попытка {attempt + 1})")
                if attempt < retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при запросе к DeepSeek API: {e}", exc_info=True)
                if attempt < retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                return None
        
        return None
    
    def generate_detailed_comment(self, context_text: str, retries: int = 2) -> Optional[str]:
        """
        Генерирует развернутый саркастичный комментарий через DeepSeek API на основе контекста
        
        Args:
            context_text: Текст контекста из нескольких сообщений
            retries: Количество попыток при ошибке
            
        Returns:
            Сгенерированный развернутый комментарий или None в случае ошибки
        """
        if not self.api_key:
            logger.error("DEEPSEEK_API_KEY не установлен")
            return None
        
        if not context_text or len(context_text.strip()) < 20:
            logger.warning("Контекст слишком короткий для анализа")
            return None
        
        prompt = self._create_detailed_prompt(context_text)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"Отправка запроса к DeepSeek API для развернутого комментария (попытка {attempt + 1})")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    comment = result['choices'][0]['message']['content'].strip()
                    logger.info(f"Успешно получен развернутый комментарий от DeepSeek: {comment[:100]}...")
                    return comment
                
                elif response.status_code == 429:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded. Status: {response.status_code}")
                    if attempt < retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.info(f"Ожидание {wait_time} секунд перед повтором...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                elif response.status_code == 401:
                    logger.error("Неверный API ключ DeepSeek")
                    return None
                
                elif response.status_code >= 500:
                    # Server error
                    logger.warning(f"Ошибка сервера DeepSeek: {response.status_code}")
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.info(f"Ожидание {wait_time} секунд перед повтором...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                else:
                    logger.error(f"Неожиданный статус ответа: {response.status_code}, {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Таймаут при запросе к DeepSeek API (попытка {attempt + 1})")
                if attempt < retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при запросе к DeepSeek API: {e}", exc_info=True)
                if attempt < retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                return None
        
        return None


def generate_sarcastic_comment_via_deepseek(text: str) -> Optional[str]:
    """
    Удобная функция-обертка для генерации саркастичных комментариев через DeepSeek
    
    Args:
        text: Текст пересланного сообщения
        
    Returns:
        Саркастичный комментарий или None в случае ошибки
    """
    client = DeepSeekClient()
    return client.generate_comment(text)


def generate_detailed_sarcastic_comment_via_deepseek(context_text: str) -> Optional[str]:
    """
    Удобная функция-обертка для генерации развернутых саркастичных комментариев через DeepSeek
    
    Args:
        context_text: Текст контекста из нескольких сообщений
        
    Returns:
        Развернутый саркастичный комментарий или None в случае ошибки
    """
    client = DeepSeekClient()
    return client.generate_detailed_comment(context_text)

