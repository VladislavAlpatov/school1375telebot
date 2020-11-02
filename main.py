import telebot
from telebot import types

nineCharList = ['9-А', '9-Б', '9-И', '9-M', '9-C', '9-Т', '9-Э']
tenCharList = ['10-А', '10-Б', '10-И', '10-Л', '10-C', '10-Э', '10-M']
elevenCharList = ['11-А', '11-Б', '11-Г', '11-Л', '11-C', '11-И', '11-M']


class MainMenuButton(types.ReplyKeyboardMarkup):
    """
    Начальная кнопка при старте
    """

    def __init__(self):
        super().__init__()
        self.add(types.KeyboardButton(text='📃Расписание📃'))
        self.add(types.KeyboardButton(text='🎱Игра🎱'))
        self.add(types.KeyboardButton(text='📰Новости📰'))


class RangeNumberInLineButton(types.InlineKeyboardMarkup):
    def __init__(self, numbers):
        super().__init__()
        for number in numbers:
            self.add(types.InlineKeyboardButton(text=str(number), callback_data=str(number)))


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

            if call.data == '9':
                self.send_message(call.message.chat.id, f'Вы учитесь в 9 классе, теперь выберите'
                                                        f' букву класса.',
                                  reply_markup=RangeNumberInLineButton(nineCharList))

            elif call.data == '10':
                self.send_message(call.message.chat.id, f'Вы учитесь в 10 классе, теперь выберите'
                                                        f' букву класса.',
                                  reply_markup=RangeNumberInLineButton(tenCharList))
            elif call.data == '11':
                self.send_message(call.message.chat.id, f'Вы учитесь в 10 классе, теперь выберите'
                                                        f' букву класса.',
                                  reply_markup=RangeNumberInLineButton(tenCharList))
                self.send_message(call.message.chat.id, f'Вы учитесь в 10 классе, теперь выберите'
                                                        f' букву класса.',
                                  reply_markup=RangeNumberInLineButton(elevenCharList))

        @self.message_handler(content_types=['text'])
        def handle_message(message):

            if message.text == '📃Расписание📃':
                self.send_message(message.chat.id, 'Пожалуйста выберите класс в котором вы обучаетесь.',
                                  reply_markup=RangeNumberInLineButton(range(9, 12)))

            elif message.text == '🎱Игра🎱':
                pass

            elif message.text == '📰Новости📰':
                pass

        self.polling()


if __name__ == '__main__':
    Bot('1495944770:AAFJJKzDhukjYLUIh9bCWYbxdYcxcd9H9OE').run()
