import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler

from schedule_parser import (
    process_and_save_excel,
    get_group_schedule_from_db,
    render_group_image,
    GroupSchedule   # ← важно добавить
)

# ==================== СОСТОЯНИЯ ====================
UPLOAD_SCHEDULE_STATE = 20

# ==================== ХЕНДЛЕРЫ ====================

async def upload_schedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало загрузки расписания"""
    await update.message.reply_text(
        "📤 Отправьте Excel-файл с расписанием (.xlsx)\n\n"
        "После отправки файл будет обработан и загружен в базу данных."
    )
    return UPLOAD_SCHEDULE_STATE


async def upload_schedule_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document or not update.message.document.file_name.endswith('.xlsx'):
        await update.message.reply_text("❌ Пожалуйста, отправьте файл .xlsx")
        return UPLOAD_SCHEDULE_STATE

    document = update.message.document
    await update.message.reply_text("⏳ Обрабатываю и загружаю расписание на завтра...")

    file = await document.get_file()
    temp_dir = "temp_schedules"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, document.file_name)

    await file.download_to_drive(file_path)

    try:
        await process_and_save_excel(file_path, context=context)  # ← передаём context
        await update.message.reply_text(
            "✅ Расписание на завтра успешно загружено!\n"
            "Уведомления отправлены студентам обновлённых групп."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при загрузке:\n{str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return ConversationHandler.END


async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена загрузки"""
    await update.message.reply_text("❌ Загрузка расписания отменена.")
    return ConversationHandler.END


async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение расписания по номеру группы"""
    if not context.args:
        await update.message.reply_text(
            "Использование:\n"
            "/schedule <номер_группы>\n\n"
            "Пример: `/schedule 1520341`"
        )
        return

    group_number = context.args[0].strip()

    await update.message.reply_text(f"🔍 Ищу расписание для группы {group_number}...")

    try:
        lessons = await get_group_schedule_from_db(group_number)

        if not lessons:
            await update.message.reply_text(f"❌ Расписание для группы {group_number} не найдено.")
            return

        # Создаём папку для изображений
        os.makedirs("temp_images", exist_ok=True)
        image_path = f"temp_images/schedule_{group_number}.png"

        # Генерируем изображение
        group_schedule = GroupSchedule(  # Нужно импортировать
            group_number=group_number,
            group_label=f"Группа {group_number}",
            direction="",
            week_label="Актуальное расписание",
            lessons=lessons
        )

        render_group_image(group_schedule, image_path)

        # Отправляем фото
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"📅 Расписание группы {group_number}",
                parse_mode='HTML'
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка:\n{str(e)}")


# ==================== СОЗДАНИЕ HANDLER'ОВ ====================

def get_schedule_handlers():
    upload_handler = ConversationHandler(
        entry_points=[CommandHandler('uploadschedule', upload_schedule_start)],
        states={
            UPLOAD_SCHEDULE_STATE: [
                MessageHandler(filters.Document.ALL, upload_schedule_file)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_upload)]
    )

    return [
        upload_handler
        # CommandHandler('schedule', get_schedule)
    ]