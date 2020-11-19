import telebot
from telebot import types
from modules import subtext
from modules import siteparser
import pyowm
import requests
from PIL import Image
import os
from pyowm.utils.config import get_default_config
from modules import dbcontrol


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

        self.__nineCharList = ('9-А', '9-Б', '9-И', '9-М', '9-Э')
        self.__tenCharList = ('10-А', '10-Б', '10-И', '10-Л', '10-Э', '10-М')
        self.__elevenCharList = ('11-А', '11-Б', '11-Г', '11-Л', '11-С', '11-И', '11-М')
        self.__callbacks = ('9', '10', '11')

        # разделы
        self.__MiscDir = RangeNumberReplyButton(['🌤Погода🌤', '😺Котики😺', '🔄Главное меню🔄'])
        self.__MainDir = RangeNumberReplyButton(['📚Школа📚', '🎲Прочее🎲'])
        self.__SchoolDir = RangeNumberReplyButton(['📃Расписание📃', '📰Новости📰', '🔄Главное меню🔄'])

        # погодник
        presets = get_default_config()
        presets['language'] = 'ru'
        self.__owm = pyowm.OWM(os.environ.get('OWN_TOKEN'), presets)

        # список админов
        self.__admins = (852250251, 500132649)

    def __str__(self):
        return f'Токен:{self.token}'

    def run(self):

        @self.message_handler(commands=['start'])
        def start_message(message):
            db = dbcontrol.DBcontrol("data_bases/banlist.db")

            if not db.user_exists(message.from_user.id):
                db.add_user(message.from_user.id, message.from_user.first_name)
                self.send_message(message.chat.id, subtext.help_message.replace("%name%", message.from_user.first_name),
                                  reply_markup=self.__MainDir)

            else:
                self.send_message(message.chat.id, "Вы уже отправляли комманду /start")

            db.close()

        @self.message_handler(commands=['ban'])
        def ban_command(message):
            if message.from_user.id in self.__admins:
                try:
                    db = dbcontrol.DBcontrol("data_bases/banlist.db")
                    line = str(message.text).split(' ')
                    db.set_ban_status(int(line[1]), True if line[2] == "true" else False)
                except Exception as e:
                    self.send_message(message.chat.id, f'⛔Не удалось произвести операциюю⛔ , код ошибки "{e}"')
            else:
                self.send_message(message.chat.id, "⛔В доступе отказано!⛔")

        @self.message_handler(commands=['db'])
        def dump_db(message):
            if message.from_user.id in self.__admins:
                try:
                    line = str(message.text).split(' ')
                    with open(f"data_bases/{line[1]}", 'rb') as f:
                        self.send_document(message.chat.id, f)
                except FileNotFoundError:
                    self.send_message(message.chat.id, f'⛔База данных  не была найдена⛔')
                except IndexError:
                    self.send_message(message.chat.id, f'⛔Нет аргумента⛔')
            else:
                self.send_message(message.chat.id, "⛔В доступе отказано!⛔")

        @self.callback_query_handler(func=lambda call: True)
        def callback_inline(call):

            if call.data == '9':
                self.send_message(call.message.chat.id, f'Теперь выберите Ваш класс. 👇',
                                  reply_markup=RangeNumberInLineButton(self.__nineCharList))

            elif call.data == '10':
                self.send_message(call.message.chat.id, f'Теперь выберите Ваш класс. 👇',
                                  reply_markup=RangeNumberInLineButton(self.__tenCharList))

            elif call.data == '11':
                self.send_message(call.message.chat.id, f'Теперь выберите Ваш класс. 👇',
                                  reply_markup=RangeNumberInLineButton(self.__elevenCharList))

            else:
                try:
                    with open(f'media/images/расписания/{call.data}.jpg', 'rb') as f:
                        self.send_message(call.message.chat.id, f"Загружаю расписание для класса {call.data}...")
                        self.send_photo(call.message.chat.id, f)

                except FileNotFoundError:
                    self.send_message(call.message.chat.id, f"Ой, я не нашёл расписание для класса {call.data} 😟")

        @self.message_handler(content_types=['text'])
        def handle_message(message):

            db = dbcontrol.DBcontrol("data_bases/banlist.db")
            user = db.get_user_ban_status(message.from_user.id)[0]
            if user[2]:
                self.send_message(message.chat.id, '⛔Ваша забись была заблокированна⛔')

            elif message.text == '📃Расписание📃':
                self.send_message(message.chat.id, 'Пожалуйста, выберите параллель, в которой Вы обучаетесь. 👇',
                                  reply_markup=RangeNumberInLineButton(range(9, 12)))

            elif message.text == '📚Школа📚':
                self.send_message(message.chat.id, 'Вы находитесь в разделе «📚Школа📚».',
                                  reply_markup=self.__SchoolDir)

            elif message.text == '🔄Главное меню🔄':
                self.send_message(message.chat.id, 'Вы вернулись в главное меню.',
                                  reply_markup=self.__MainDir)

            elif message.text == '📰Новости📰':
                site = siteparser.News()
                self.send_message(message.chat.id, f'*{site.getLastNewsTitle()}*\n\n{site.getLastNewsText()}',
                                  parse_mode='Markdown')

            elif message.text == '🎲Прочее🎲':
                self.send_message(message.chat.id, 'В находитесь в разделе «🎲Прочее 🎲».',
                                  reply_markup=self.__MiscDir)

            elif message.text == '🌤Погода🌤':
                try:
                    mgr = self.__owm.weather_manager()
                    w = mgr.weather_at_place('Москва').weather
                    self.send_message(message.chat.id, f"*Погода на сегодня.*\n\n"
                                                       f"*Статус:* {w.detailed_status}\n"
                                                       f"*Температура:* {w.temperature('celsius')['temp']} ℃\n"
                                                       f"*Скорость ветра:* {w.wind()['speed']} м\\с\n"
                                                       f"*Влажность:* {w.humidity}%\n*Облачность:* {w.clouds}%",
                                      parse_mode='Markdown')
                except Exception:
                    self.send_message(message.chat.id, '⛔Увы я не смог получить данные о погоде, попробуйте позже!⛔')

            elif message.text == '⚠COVID-19⚠':
                site = siteparser.Covid19()
                self.send_message(
                    message.chat.id,
                    f"*COVID*\n\nВсего заболело: *{site.getAllInfected()}* человек.\n"
                    f"Всего умерло: *{site.getAllDied()}* человек.\n"
                    f"🤒Зарозилось за день: *{site.getInfectedInLastDay()}* человек.🤒\n"
                    f"😎Выздаровело всего: *{site.getAllHealed()}* человек.😎",
                    parse_mode='Markdown')

            elif message.text == '😺Котики😺':
                try:
                    image = requests.get('https://thiscatdoesnotexist.com/')

                    with open(f'{message.chat.id}.jpg', 'wb') as f:
                        f.write(image.content)

                    with open(f'{message.chat.id}.jpg', 'rb') as f:
                        self.send_photo(message.chat.id, f)

                    os.remove(f'{message.chat.id}.jpg')
                except PermissionError:
                    self.send_message(message.chat.id, "⛔Вы отправляете сообщения слишком быстро!⛔")

            else:
                self.send_message(message.chat.id, 'Жаль, что я плохо понимаю людей😥')
            db.close()
        self.polling()


if __name__ == '__main__':
    Bot(os.environ.get('TOKEN')).run()
