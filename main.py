import logging
import os
from enum import Enum, auto
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Включаем логирование, чтобы видеть ошибки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот. Напиши мне что-нибудь.')

class States(Enum):
    UPLOAD = auto()

# /upload
async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Отправь фото!')
    return States.UPLOAD

# Загрузка файла
async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive("Files/user_photo.jpg")
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Принято в обработку')
    return ConversationHandler.END

# /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Отмена.')
    return ConversationHandler.END

upload_foto = ConversationHandler(
    entry_points=[CommandHandler('upload', upload_start)],
    states= {
        States.UPLOAD: [MessageHandler(filters.PHOTO, upload_file)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)



keyboard = [
    [
        InlineKeyboardButton('ФИИТ', callback_data=0),
        InlineKeyboardButton('МОАИС', callback_data=1)
    ],
    [
        InlineKeyboardButton('ПИвЗ', callback_data=2),
        InlineKeyboardButton('ПИвЭ', callback_data=3)
    ]
]

fkeys = InlineKeyboardMarkup(keyboard)

async def choose_f(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Выберите направление:', reply_markup=fkeys)

async def choosing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы выбрали кнопку {data}")
    print(data)

if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')
    # Создаем приложение и передаем ему токен
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчики команд и сообщений
    app.add_handler(CommandHandler("start", start))

    app.add_handler(upload_foto)

    app.add_handler(CommandHandler("choose", choose_f))
    app.add_handler(CallbackQueryHandler(choosing_handler))

    print("Бот запущен...")
    # Запускаем бота в режиме поллинга (опроса сервера)
    app.run_polling()