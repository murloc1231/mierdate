from telebot.handler_backends import State, StatesGroup

class YourInfoState(StatesGroup):
    age = State()
    gender = State()
    preference = State()
    city = State()
    name = State()
    about_myself = State()
    photo = State()
    more = State()
