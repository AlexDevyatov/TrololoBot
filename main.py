"""
Основной файл Telegram бота для генерации саркастичных комментариев
на пересланные сообщения
"""
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

import config
from comment_generator import generate_detailed_sarcastic_comment
from context_manager import context_manager


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Класс для ограничения частоты отправки сообщений"""
    
    def __init__(self, max_messages: int, time_window: int):
        """
        Args:
            max_messages: Максимальное количество сообщений
            time_window: Временное окно в секундах
        """
        self.max_messages = max_messages
        self.time_window = time_window
        self.user_messages = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Проверяет, разрешено ли пользователю отправить сообщение
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если разрешено, False если превышен лимит
        """
        now = datetime.now()
        user_history = self.user_messages[user_id]
        
        # Удаляем старые записи вне временного окна
        cutoff_time = now - timedelta(seconds=self.time_window)
        user_history[:] = [msg_time for msg_time in user_history if msg_time > cutoff_time]
        
        # Проверяем лимит
        if len(user_history) >= self.max_messages:
            return False
        
        # Добавляем текущее время
        user_history.append(now)
        return True
    
    def get_wait_time(self, user_id: int) -> int:
        """
        Возвращает время ожидания до следующего разрешенного сообщения
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Время ожидания в секундах
        """
        user_history = self.user_messages[user_id]
        if not user_history:
            return 0
        
        oldest_message = min(user_history)
        wait_until = oldest_message + timedelta(seconds=self.time_window)
        wait_time = (wait_until - datetime.now()).total_seconds()
        
        return max(0, int(wait_time))


# Создаем экземпляр rate limiter
rate_limiter = RateLimiter(
    max_messages=config.RATE_LIMIT_MESSAGES,
    time_window=config.RATE_LIMIT_WINDOW
)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    welcome_message = (
        "Привет! Я бот для саркастичного анализа пересланных сообщений.\n\n"
        "Как использовать:\n"
        "1. Пересылай мне сообщения - я буду сохранять их в контекст\n"
        "2. Используй /analyze для генерации развернутого саркастичного комментария на основе накопленного контекста\n"
        "3. Используй /clear для очистки контекста\n\n"
        "Контекст автоматически очищается через 30 минут бездействия или при достижении 10 сообщений."
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"User {user_id} started the bot")


async def handle_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /analyze - генерирует развернутый комментарий на основе контекста"""
    user_id = update.effective_user.id
    message = update.message
    
    # Проверяем rate limiting
    if not rate_limiter.is_allowed(user_id):
        wait_time = rate_limiter.get_wait_time(user_id)
        warning_message = (
            f"Слишком много запросов. Пожалуйста, подождите {wait_time} секунд."
        )
        await message.reply_text(warning_message)
        logger.warning(f"Rate limit exceeded for user {user_id}")
        return
    
    # Проверяем наличие контекста
    if not context_manager.has_context(user_id):
        await message.reply_text(
            "У вас нет накопленного контекста. Пересылайте сообщения, чтобы создать контекст для анализа."
        )
        logger.info(f"User {user_id} tried to analyze without context")
        return
    
    try:
        # Получаем контекст
        context_text = context_manager.get_context_text(user_id)
        
        if not context_text:
            await message.reply_text(
                "Контекст пуст или истек. Пересылайте новые сообщения."
            )
            return
        
        msg_count = context_manager.get_message_count(user_id)
        await message.reply_text(
            f"Анализирую контекст из {msg_count} сообщений... Это может занять некоторое время."
        )
        
        logger.info(f"Generating detailed comment for user {user_id} with {msg_count} messages in context")
        
        # Генерируем развернутый саркастичный комментарий
        try:
            comment = generate_detailed_sarcastic_comment(context_text)
            
            if not comment:
                logger.error("Не удалось сгенерировать развернутый комментарий")
                await message.reply_text(
                    "Не удалось сгенерировать комментарий. Проверьте настройки API или попробуйте позже."
                )
                return
            
            # Отправляем развернутый комментарий
            await message.reply_text(comment)
            logger.info(f"Sent detailed sarcastic comment to user {user_id}")
            
        except Exception as gen_error:
            logger.error(f"Error generating detailed comment for user {user_id}: {gen_error}", exc_info=True)
            await message.reply_text(
                "Произошла ошибка при генерации комментария. Попробуйте позже."
            )
        
    except Exception as e:
        logger.error(f"Error processing analyze command for user {user_id}: {e}", exc_info=True)
        await message.reply_text(
            "Произошла ошибка при обработке команды. Попробуйте позже."
        )


async def handle_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /clear - очищает контекст пользователя"""
    user_id = update.effective_user.id
    message = update.message
    
    context_manager.clear_context(user_id)
    await message.reply_text("Контекст очищен. Можете начать собирать новый контекст.")
    logger.info(f"User {user_id} cleared context")


async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик пересланных сообщений - сохраняет их в контекст
    
    Args:
        update: Объект обновления от Telegram
        context: Контекст бота
    """
    user_id = update.effective_user.id
    message = update.message
    
    if not message:
        return
    
    # Проверяем, что сообщение переслано
    # В python-telegram-bot 20+ пересланные сообщения имеют атрибут forward_origin
    if not message.forward_origin:
        logger.debug(f"Сообщение от пользователя {user_id} не является пересланным")
        return
    
    try:
        # Получаем текст сообщения
        text = message.text or message.caption or ""
        
        if not text:
            # Если нет текста, но есть медиа, сообщаем об этом
            if message.photo or message.video or message.document:
                await message.reply_text(
                    "Переслано медиа без подписи. К сожалению, я анализирую только текстовое содержание."
                )
                logger.info(f"Received forwarded media without caption from user {user_id}")
            else:
                logger.debug(f"Received forwarded message without text from user {user_id}")
            return
        
        logger.info(f"Received forwarded message from user {user_id}: {text[:50]}...")
        
        # Добавляем сообщение в контекст
        context_manager.add_message(user_id, text, message.message_id)
        
        msg_count = context_manager.get_message_count(user_id)
        await message.reply_text(
            f"✓ Сообщение добавлено в контекст ({msg_count}/{config.CONTEXT_MAX_MESSAGES}). "
            f"Используйте /analyze для генерации комментария."
        )
        logger.info(f"Added message to context for user {user_id}. Total messages: {msg_count}")
        
    except Exception as e:
        logger.error(f"Error processing forwarded message from user {user_id}: {e}", exc_info=True)
        await message.reply_text(
            "Произошла ошибка при обработке сообщения. Попробуйте позже."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


def main() -> None:
    """Основная функция запуска бота"""
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен! Установите его в переменных окружения или .env файле")
        return
    
    # Проверяем наличие API ключа DeepSeek (предупреждение, не критично)
    if not config.DEEPSEEK_API_KEY:
        logger.warning(
            "DEEPSEEK_API_KEY не установлен! "
            "Бот будет использовать локальную генерацию комментариев вместо DeepSeek API. "
            "Для использования DeepSeek API установите ключ в переменных окружения или .env файле"
        )
    else:
        logger.info("DeepSeek API ключ найден, будет использоваться API для генерации комментариев")
    
    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("analyze", handle_analyze))
    application.add_handler(CommandHandler("clear", handle_clear))
    
    # Регистрируем обработчик пересланных сообщений
    # Фильтр для пересланных сообщений (в версии 20+ используется FORWARDED)
    # Обрабатываем пересланные сообщения с текстом или подписями к медиа
    forwarded_filter = filters.FORWARDED & (filters.TEXT | filters.CAPTION)
    
    application.add_handler(
        MessageHandler(forwarded_filter, handle_forwarded_message)
    )
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Периодическая очистка истекших контекстов
    async def cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Периодическая задача для очистки истекших контекстов"""
        context_manager.cleanup_expired_contexts()
    
    # Запускаем периодическую задачу очистки каждые 10 минут
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(cleanup_job, interval=600, first=600)  # 600 секунд = 10 минут
    
    logger.info("Бот запущен и готов к работе")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

