import telebot


bot = telebot.TeleBot(token='')

if __name__ == '__main__':
    bot.polling()
