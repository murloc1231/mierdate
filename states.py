from telebot.handler_backends import State, StatesGroup


class YourInfoState(StatesGroup):
    age = State()
    gender = State()
    preferences = State()
    city = State()
    name = State()
    description = State()
    photo = State()
