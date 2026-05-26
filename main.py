import logging
import os
from enum import Enum, auto
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes, \
    CallbackQueryHandler

from config import BOT_TOKEN
from database import db

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# ====================== ТЕСТОВЫЕ ФУНКЦИИ ======================

async def test_db_insert():
    try:
        await db.execute(
            "INSERT INTO users (telegram_id, username) VALUES ($1, $2) ON CONFLICT (telegram_id) DO NOTHING",
            123456789, "test_user"
        )
        print("✅ Тестовая запись добавлена")
    except Exception as e:
        print(f"❌ Ошибка insert: {e}")


async def test_db_select():
    try:
        rows = await db.fetch("SELECT * FROM users LIMIT 5")
        print(f"✅ Найдено записей: {len(rows)}")
        for row in rows:
            print(dict(row))
    except Exception as e:
        print(f"❌ Ошибка select: {e}")


# ====================== ХЕНДЛЕРЫ ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот. Напиши мне что-нибудь.')


# ====================== Запуск ======================

if __name__ == '__main__':
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    async def on_startup():
        try:
            await db.connect()
            print("✅ Успешное подключение к PostgreSQL")

            # Тесты
            # await test_db_insert()
            # await test_db_select()

        except Exception as e:
            print(f"❌ Критическая ошибка при запуске: {e}")
            raise

    # Запускаем стартовые задачи
    import asyncio

    asyncio.get_event_loop().run_until_complete(on_startup())

    # ====================== ИМПОРТ ХЕНДЛЕРОВ ======================
    from handlers.schedule_handlers import get_schedule_handlers
    from handlers.registration_handlers import get_registration_handlers

    # ====================== РЕГИСТРАЦИЯ ======================
    schedule_handlers = get_schedule_handlers()
    for handler in schedule_handlers:
        app.add_handler(handler)
    handlers = get_registration_handlers()
    for handler in handlers:
        app.add_handler(handler)

    # Регистрация хендлеров
    # app.add_handler(CommandHandler("start", start))

    # app.add_handler(upload_foto)
    # app.add_handler(CommandHandler("choose", choose_f))
    # app.add_handler(CallbackQueryHandler(choosing_handler))

    print("Бот запущен...")
    app.run_polling()