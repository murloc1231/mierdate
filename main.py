from telebot import TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

from database.database import SQLiteDatabase

state_storage = StateMemoryStorage()
bot = TeleBot(token='', state_storage=state_storage)
bot.add_custom_filter(custom_filters.StateFilter(bot))
db = SQLiteDatabase('./database/database.sqlite', pool_size=10)


@bot.message_handler(commands=['start'])
def start(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    with db.get_cursor() as cursor:
        username = cursor.execute(
            'SELECT id FROM users WHERE users.tg_username = ?',
            [message.from_user.username],
        ).fetchone()

    if not username:
        keyboard.add(KeyboardButton(text='Создать анкету'))

    bot.send_message(
        message.chat.id,
        f'Welcome to Mierdate, {message.from_user.full_name}',
        reply_markup=keyboard,
    )


if __name__ == '__main__':
    bot.polling()
