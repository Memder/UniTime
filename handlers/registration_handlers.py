import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler

from database import db
from schedule_parser import render_group_image, GroupSchedule, get_tomorrow_schedule_for_user

# Состояния
CHOOSING_COURSE = 1
CHOOSING_GROUP = 2

# ==================== КЛАВИАТУРЫ ====================

async def get_courses_keyboard():
    keyboard = [
        [InlineKeyboardButton("1 курс", callback_data="course_1")],
        [InlineKeyboardButton("2 курс", callback_data="course_2")],
        [InlineKeyboardButton("3 курс", callback_data="course_3")],
        [InlineKeyboardButton("4 курс", callback_data="course_4")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def get_groups_keyboard(course: int):
    async with db.pool.acquire() as conn:
        groups = await conn.fetch(
            'SELECT id_g, group_number FROM "Group" WHERE course = $1 ORDER BY group_number',
            course
        )
    keyboard = []
    for g in groups:
        keyboard.append([InlineKeyboardButton(str(g['group_number']), callback_data=f"group_{g['id_g']}")])
    return InlineKeyboardMarkup(keyboard)


# ==================== ХЕНДЛЕРЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    # Проверяем, зарегистрирован ли пользователь
    async with db.pool.acquire() as conn:
        exists = await conn.fetchval(
            'SELECT id_us FROM Users WHERE telegram_id = $1', telegram_id
        )

    if exists:
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n"
            "Ты уже зарегистрирован.\n"
            "Используй /schedule чтобы посмотреть расписание на завтра."
        )
    else:
        await update.message.reply_text(
            "Добро пожаловать! 🎓\n\n"
            "Для начала выбери свой курс:",
            reply_markup=await get_courses_keyboard()
        )
        return CHOOSING_COURSE


async def choose_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    course = int(query.data.split('_')[1])
    context.user_data['course'] = course

    await query.edit_message_text(
        text=f"Выбран курс: {course}\n\nТеперь выбери свою группу:",
        reply_markup=await get_groups_keyboard(course)
    )
    return CHOOSING_GROUP


async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split('_')[1])
    telegram_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name

    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO Users (telegram_id, id_group, id_role, messenger_id)
            VALUES ($1, $2, 
                (SELECT id_role FROM Roles WHERE dol = 'студент'),
                $3)
            ON CONFLICT (telegram_id) 
            DO UPDATE SET id_group = $2
            """,
            telegram_id, group_id, username
        )

    await query.edit_message_text(
        "✅ Регистрация завершена!\n\n"
        "Теперь ты можешь использовать команду /schedule"
    )
    return ConversationHandler.END


# ==================== РАСПИСАНИЕ НА ЗАВТРА ====================

async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    lessons = await get_tomorrow_schedule_for_user(telegram_id)

    if not lessons:
        await update.message.reply_text(
            "❌ Ты ещё не выбрал группу или расписание на завтра отсутствует."
        )
        return

    # Создаём объект для рендера
    group_schedule = GroupSchedule(
        group_number="",
        group_label="Расписание на завтра",
        direction="",
        week_label="Завтра",
        lessons=lessons
    )

    os.makedirs("temp_images", exist_ok=True)
    image_path = f"temp_images/schedule_tomorrow_{telegram_id}.png"

    render_group_image(group_schedule, image_path)

    with open(image_path, 'rb') as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="📅 Твоё расписание на завтра"
        )


# ==================== СОЗДАНИЕ HANDLER'ОВ ====================

def get_registration_handlers():
    reg_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_COURSE: [CallbackQueryHandler(choose_course, pattern="^course_")],
            CHOOSING_GROUP: [CallbackQueryHandler(choose_group, pattern="^group_")],
        },
        fallbacks=[]
    )

    return [
        reg_handler,
        CommandHandler('schedule', get_schedule)
    ]