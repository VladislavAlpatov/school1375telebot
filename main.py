# coding=utf-8
import telebot
from telebot import types
from modules import subtext
from modules import siteparser
import requests
from PIL import Image
import os


class RangeNumberInLineButton(types.InlineKeyboardMarkup):
    def __init__(self, numbers):
        super().__init__()
        for number in numbers:
            self.add(types.InlineKeyboardButton(text=str(number), callback_data=str(number)))


class RangeNumberReplyButton(types.ReplyKeyboardMarkup):
    def __init__(self, numbers):
        super().__init__()
        for number in numbers:
            self.add(types.KeyboardButton(text=str(number)))


class Bot(telebot.TeleBot):
    """
    Класс нашего бота
    """

    def __init__(self, token: str):
        super().__init__(token)
        self.__nineCharList = ('9-А', '9-Б', '9-И', '9-M', '9-C', '9-Э')
        self.__tenCharList = ('10-А', '10-Б', '10-И', '10-Л', '10-C', '10-Э', '10-M')
        self.__elevenCharList = ('11-А', '11-Б', '11-Г', '11-Л', '11-C', '11-И', '11-M')
        self.__callbacks = ('9', '10', '11')
        print('Запущен!')

    def __str__(self):
        return f'Токен:{self.token}'

    def run(self):

        @self.message_handler(commands=['start'])
        def start_message(message):
            name = message.from_user.first_name
            self.send_message(message.chat.id, subtext.help_message.replace("%name%", name),
                              reply_markup=RangeNumberReplyButton(['📚Школа📚', 'Прочее']))

        @self.callback_query_handler(func=lambda call: True)
        def callback_inline(call):

            if call.data == '9':
                self.send_message(call.message.chat.id, f'Вы учитесь в 9 классе, теперь выберите'
                                                        ' букву класса.',
                                  reply_markup=RangeNumberInLineButton(self.__nineCharList))

            elif call.data == '10':
                self.send_message(call.message.chat.id, f'Вы учитесь в 10 классе, теперь выберите'
                                                        ' букву класса.',
                                  reply_markup=RangeNumberInLineButton(self.__tenCharList))

            elif call.data == '11':
                self.send_message(call.message.chat.id, f'Вы учитесь в 11 классе, теперь выберите'
                                                        ' букву класса.',
                                  reply_markup=RangeNumberInLineButton(self.__elevenCharList))

            else:
                try:
                    print(f'media/images/расписания/{call.data}.jpg')
                    with open(f'media/images/расписания/{call.data}.jpg', 'rb') as f:
                        self.send_message(call.message.chat.id, f"Загружаю расписание для класса {call.data}...")
                        self.send_photo(call.message.chat.id, f)
                except FileNotFoundError:
                    self.send_message(call.message.chat.id, f"Ой, я не нашёл расписание для класса {call.data} 😟")

        @self.message_handler(content_types=['text'])
        def handle_message(message):

            if message.text == '📃Расписание📃':
                self.send_message(message.chat.id, 'Пожалуйста выберите класс в котором вы обучаетесь.',
                                  reply_markup=RangeNumberInLineButton(range(9, 12)))

            elif message.text == '📚Школа📚':
                self.send_message(message.chat.id, 'Вы перешли в "Школьный" раздел.',
                                  reply_markup=RangeNumberReplyButton(['📃Расписание📃',
                                                                       '📰Новости📰',
                                                                       '🔄Главное меню🔄']))

            elif message.text == '🔄Главное меню🔄':
                self.send_message(message.chat.id, 'Вы вернулись в главное меню.',
                                  reply_markup=RangeNumberReplyButton(['📚Школа📚',
                                                                       '🎲Прочее🎲']))

            elif message.text == '📰Новости📰':
                site = siteparser.News()
                self.send_message(message.chat.id, f'*{site.getLastNewsTitle()}*\n\n{site.getLastNewsText()}',
                                  parse_mode='Markdown')

            elif message.text == '🎲Прочее🎲':
                self.send_message(message.chat.id, 'Вы перешли в раздел "🎲Прочее🎲".',
                                  reply_markup=RangeNumberReplyButton(['🤣Анекдоты🤣',
                                                                       '😺Котики😺',
                                                                       '🔄Главное меню🔄']))

            elif message.text == '🤣Анекдоты🤣':
                self.send_message(message.chat.id, siteparser.Jokes().getJoke())

            elif message.text == '😺Котики😺':
                image = requests.get('https://thiscatdoesnotexist.com/')

                with open(f'{message.chat.id}.jpg', 'wb') as f:
                    f.write(image.content)

                with open(f'{message.chat.id}.jpg', 'rb') as f:
                    self.send_photo(message.chat.id, f)

                os.remove(f'{message.chat.id}.jpg')

            else:
                self.send_message(message.chat.id, 'Жаль, что я плохо понимаю людей😥')

        self.polling()


if __name__ == '__main__':
    Bot('1347415058:AAFp6XsJgeyMaTCa1fK7A8G4qf-y20VjNno').run()
