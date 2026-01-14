"""
Конфигурационный файл для Telegram бота
"""
import os
from dotenv import load_dotenv

# Загружаем переменные из creds.txt
load_dotenv('creds.txt')
# Также пытаемся загрузить из .env (для обратной совместимости)
load_dotenv()

# Токен бота (получить у @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# DeepSeek API конфигурация
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = 'deepseek-chat'
DEEPSEEK_TIMEOUT = 30  # Таймаут запроса в секундах
DEEPSEEK_MAX_TOKENS = 500  # Максимальная длина ответа для развернутых комментариев
DEEPSEEK_TEMPERATURE = 0.7  # Температура для генерации

# Настройки контекста
CONTEXT_MAX_MESSAGES = 10  # Максимальное количество сообщений в контексте
CONTEXT_TIMEOUT_MINUTES = 30  # Таймаут контекста в минутах
CONTEXT_MAX_TOKENS = 4000  # Максимальная длина контекста в токенах

# Настройки rate limiting
RATE_LIMIT_MESSAGES = 5  # Максимальное количество сообщений
RATE_LIMIT_WINDOW = 60   # Временное окно в секундах

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'bot.log'

