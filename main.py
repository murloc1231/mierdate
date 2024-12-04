from typing import TypedDict
from telebot import TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from database.database import SQLiteDatabase
from states import SearchState, YourInfoState
import json
import pickle
import settings
from gensim.models.doc2vec import Doc2Vec


class ProfileInfo(TypedDict):
    name: str
    city: str
    gender: str
    age: int
    description: str


class FullProfile(ProfileInfo):
    id: int
    chat_id: int
    photo: str
    preferences: str


state_storage = StateMemoryStorage()
bot = TeleBot(
    token='7564254378:AAG9PPGvZ50KtGYaD1gX2hyvociCJh7m-ZI', state_storage=state_storage
)
bot.add_custom_filter(custom_filters.StateFilter(bot))
db = SQLiteDatabase(settings.DB_PATH, pool_size=10)
model: Doc2Vec = Doc2Vec.load(settings.MODEL_PATH)
with open(settings.PROFILES_PATH, 'r', encoding='utf-8') as file:
    cities: list[str] = json.load(file)['cities']
with open(settings.VECTORS_PROFILES_PATH, 'br') as file:
    vectors_profiles = pickle.load(file)
with open(settings.PROFILES_VECTORS_PATH, 'br') as file:
    profiles_vectors = pickle.load(file)


@bot.message_handler(commands=['start'])
def start(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    with db.get_cursor() as cursor:
        user_id = cursor.execute(
            'SELECT id FROM users WHERE users.id = ?',
            [message.from_user.id],
        ).fetchone()

    if not user_id:
        keyboard.add('Создать анкету')
    else:
        keyboard.add('Поиск')

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
        return bot.send_message(message.chat.id, 'Введите число')

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
        return bot.send_message(message.chat.id, 'Неверное значение')

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
        return bot.send_message(message.chat.id, 'Неверное значение')

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['preferences'] = message.text

    bot.send_message(
        chat_id=message.chat.id,
        text='Напишите свой город',
        reply_markup=ReplyKeyboardRemove(),
    )

    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.city,
    )


@bot.message_handler(state=YourInfoState.city)
def save_city(message: Message):
    city = message.text
    if city.isdigit() or city.lower().capitalize() not in cities:
        return bot.send_message(message.chat.id, 'Такого города нет')

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['city'] = city.lower().capitalize()

    bot.send_message(
        chat_id=message.chat.id, text='Напишите несколько предложений о себе'
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
        return bot.send_message(message.chat.id, 'Описание слишком короткое')

    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data['description'] = description

    bot.send_message(chat_id=message.chat.id, text='Отправьте свое фото')

    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.photo,
    )


def save_photo_on_disk(photo, filename):
    with open(f'./photos/{filename}', 'bw') as bin_file:
        bin_file.write(photo)


def read_photo(filename):
    with open(f'./photos/{filename}', 'br') as bin_file:
        return bin_file.read()


@bot.message_handler(state=YourInfoState.photo, content_types=['photo'])
def save_photo(message: Message):
    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        filename = f'{message.from_user.id}.jpg'
        save_photo_on_disk(downloaded_file, filename)
        data['photo'] = filename

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add('Да', 'Нет')
        profile_text = build_profile_text(data)
        bot.send_photo(
            chat_id=message.chat.id,
            photo=downloaded_file,
            caption=profile_text,
        )
        bot.send_message(
            chat_id=message.chat.id,
            text='Вот ваша анкета. Все верно?',
            reply_markup=keyboard,
        )

    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=YourInfoState.confirmation,
    )


@bot.message_handler(state=YourInfoState.confirmation)
def profile_confirmation(message: Message):
    if message.text not in ['Да', 'Нет']:
        return bot.send_message(message.chat.id, 'Неверное значение')

    if message.text == 'Да':
        with bot.retrieve_data(
            user_id=message.from_user.id, chat_id=message.chat.id
        ) as data:
            data['id'] = message.from_user.id
            data['chat_id'] = message.chat.id
            save_profile(data)

        bot.set_state(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            state=SearchState.search,
        )
    else:
        bot.send_message(
            message.chat.id, 'Введите имя', reply_markup=ReplyKeyboardRemove()
        )
        bot.set_state(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            state=YourInfoState.name,
        )


def save_profile(profile: FullProfile):
    with db.get_cursor() as cursor:
        save_profile_query = '''
        INSERT INTO users(
            id, name, age, city, gender,
            preferences, description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(
            save_profile_query,
            [
                profile['id'],
                profile['chat_id'],
                profile['name'],
                profile['age'],
                profile['city'],
                profile['gender'],
                profile['preferences'],
                profile['description'],
            ],
        )


def build_profile_text(profile: ProfileInfo):
    profile_text = f"{profile['name']}, {profile['age']}, {profile['city']}\n"
    profile_text += f"{profile['description']}"
    return profile_text


def build_search_keyboard():
    keyboard = ReplyKeyboardMarkup()
    keyboard.add('❤️', '💔', '💤')
    return keyboard


def get_next_profile(user_id):
    with db.get_cursor() as cursor:
        current_profile_idx = cursor.execute(
            'SELECT current_profile_idx FROM users WHERE users.id = ?', user_id
        ).fetchone()
    model.dv.most_similar(profiles_vectors[user_id])


def send_profile(message: Message, profile: FullProfile):
    profile_text = build_profile_text(profile)
    bot.send_photo(
        message.chat.id, caption=profile_text, reply_markup=build_search_keyboard()
    )


def like_profile():
    pass


def dislike_profile():
    pass


@bot.message_handler(state=SearchState.search)
def search(message: Message):
    if message.text not in ('❤️', '💔', '💤'):
        return

    if message.text == '❤️':
        next_profile = like_profile()
    elif message.text == '💔':
        next_profile = dislike_profile()
    else:
        pass

    send_profile(message=message, profile=next_profile)


@bot.message_handler(content_types='text')
def message_reply(message: Message):
    if message.text in ['Создать анкету', 'Заполнить анкету заново']:
        bot.set_state(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            state=YourInfoState.name,
        )
        bot.send_message(
            message.chat.id,
            'Введите имя',
            reply_markup=ReplyKeyboardRemove(),
        )
    elif message.text == 'Поиск':
        send_profile()
        bot.set_state(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            state=SearchState.search,
        )


if __name__ == '__main__':
    bot.polling()
