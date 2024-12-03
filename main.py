from telebot import TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database.database import SQLiteDatabase
from states import YourInfoState
import json

state_storage = StateMemoryStorage()
bot = TeleBot(
    token='7564254378:AAG9PPGvZ50KtGYaD1gX2hyvociCJh7m-ZI', state_storage=state_storage
)
bot.add_custom_filter(custom_filters.StateFilter(bot))
db = SQLiteDatabase('./database/database.sqlite', pool_size=10)
with open('./profiles/origin_data.json', 'r', encoding='utf-8') as file:
    cities: list[str] = json.load(file)['cities']


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

    bot.send_message(message.chat.id, 'Введите возраст')
    
    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.age,
    )


@bot.message_handler(state=YourInfoState.age)
def save_age(message: Message):
    if message.text.isalpha():
        return bot.send_message(
            message.chat.id, 'Введите число'
        )

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['age'] = int(message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Мужчина', 'Женщина')
    bot.send_message(message.chat.id, 'Выберите пол', reply_markup=keyboard)
    
    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.gender,
    )


@bot.message_handler(state=YourInfoState.gender)
def save_gender(message: Message):
    if message.text not in ['Мужчина', 'Женщина']:
        return bot.send_message(
            message.chat.id, 'Неверное значение'
        )

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['gender'] = message.text
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Мужчины', 'Женщины')
    bot.send_message(message.chat.id, 'Кого ищете?', reply_markup=keyboard)
    
    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.preferences,
    )


@bot.message_handler(state=YourInfoState.preferences)
def save_preferences(message: Message):
    if message.text not in ['Мужчины', 'Женщины']:
        return bot.send_message(
            message.chat.id, 'Неверное значение'
        )

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['preferences'] = message.text

    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.city,
    )


@bot.message_handler(state=YourInfoState.city)
def save_city(message: Message):
    city = message.text
    if city.isdigit() or city.lower().capitalize() not in cities:
        return bot.send_message(
            message.chat.id, 'Такого города нет'
        )

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['city'] = city.lower().capitalize()
        
    bot.send_message(
        chat_id=message.chat.id,
        text='Напишите несколько предложений о себе'
    )
    
    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.description,
    )


@bot.message_handler(state=YourInfoState.description)
def save_description(message: Message):
    description = message.text
    if len(description) < 20:
        return bot.send_message(
            message.chat.id, 'Описание слишком короткое'
        )

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['description'] = description

    bot.send_message(
        chat_id=message.chat.id,
        text='Отправьте свое фото'
    )

    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.photo,
    )


def save_photo_on_disk(photo, filename):
	with open(f'./photos/{filename}', 'wb') as bin_file:
		bin_file.write(photo)
        

@bot.message_handler(state=YourInfoState.photo, content_types=['photo'])
def save_photo(message: Message):
    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        filename = file_info.file_path.split('/')[1]
        save_photo_on_disk(downloaded_file, filename)
        data['description'] = filename
    



@bot.message_handler(content_types='text')
def message_reply(message: Message):
    if message.text in ['Создать анкету', 'Заполнить анкету заново']:
        bot.set_state(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            state=YourInfoState.photo,
        )
        bot.send_message(message.chat.id, 'Введите имя')


if __name__ == '__main__':
    bot.polling()
