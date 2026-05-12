from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

fac_keyboard = [
    [
        InlineKeyboardButton('ИПИТ', callback_data=1)
    ]
]
course_keyboard = [
    [
        InlineKeyboardButton("1", callback_data=1),
        InlineKeyboardButton("2", callback_data=2)
    ],
    [
        InlineKeyboardButton("3", callback_data=3),
        InlineKeyboardButton("4", callback_data=4)
    ]
]
group_keyboard = [
    [
        InlineKeyboardButton("1520341", callback_data=1),
        InlineKeyboardButton("21520441", callback_data=2)
    ],
    [
        InlineKeyboardButton("1520741", callback_data=3),
        InlineKeyboardButton("1520541", callback_data=4)
    ]
]


