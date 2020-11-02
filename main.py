import telebot
from telebot import types


class MainMenuButton(types.ReplyKeyboardMarkup):
    """
    Начальная кнопка при старте
    """
    def __init__(self):
        super().__init__()
        self.add(types.KeyboardButton(text='📃Расписание📃'))
        self.add(types.KeyboardButton(text='🎱Игра🎱'))
        self.add(types.KeyboardButton(text='📰Новости📰'))


class Bot(telebot.TeleBot):
    """
    Класс нашего бота
    """
    def __init__(self, token: str):
        super().__init__(token)
        print('Запущен!')

    def __str__(self):
        return f'Токен:{self.token}'

    def run(self):

        @self.message_handler(commands=['start'])
        def start_message(message):
            self.send_message(message.chat.id, 'Я могу говорить?', reply_markup=MainMenuButton())

        @self.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            pass

        @self.message_handler(content_types=['text'])
        def handle_message(message):

            if message.text == '📃Расписание📃':
                pass

            elif message.text == '🎱Игра🎱':
                pass

            elif message.text == '📰Новости📰':
                pass

        self.polling()


if __name__ == '__main__':
    Bot('тут токен').run()
