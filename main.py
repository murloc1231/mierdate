from telebot import TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database.database import SQLiteDatabase
from states import YourInfoState

state_storage = StateMemoryStorage()
bot = TeleBot(
    token='7564254378:AAG9PPGvZ50KtGYaD1gX2hyvociCJh7m-ZI', state_storage=state_storage
)
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


@bot.message_handler(state=YourInfoState.name)
def save_name(message: Message):
    if len(message.text) < 2 or len(message.text) > 15:
        return bot.send_message(
            message.chat.id, 'Имя должно быть длиннее 1 символа и короче 16'
        )

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['name'] = message.text

    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.age,
    )


@bot.message_handler(content_types='text')
def message_reply(message: Message):
    if message.text in ['Создать анкету', 'Заполнить анкету заново']:
        bot.set_state(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            state=YourInfoState.name,
        )
        bot.send_message(message.chat.id, 'Введите имя')


if __name__ == '__main__':
    bot.polling()
