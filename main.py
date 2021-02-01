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
from time import sleep


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
    Основной класс бота
    """

    def __init__(self, token: str, owm_token: str):
        super().__init__(token)

        self.__nineCharList = ('9-А', '9-Б', '9-И', '9-М', '9-Э')
        self.__tenCharList = ('10-А', '10-Б', '10-И', '10-Л', '10-Э', '10-М')
        self.__elevenCharList = ('11-А', '11-Б', '11-Г', '11-Л', '11-С', '11-И', '11-М')
        self.__callbacks = ('9', '10', '11')

        # разделы
        self.dirs = {
            '🔄Главное меню🔄': RangeNumberReplyButton(['📚Школа📚', '🎲Прочее🎲', '❓Помощь❓']),

            '📚Школа📚': RangeNumberReplyButton(['📃Расписание📃', '📰Новости📰', '🔄Главное меню🔄']),

            '❓Помощь❓': RangeNumberReplyButton(('👤Аккаунт👤', '⚙️Команды⚙️', '💬Контакты💬', '©️GitHub©️',
                                                '🔄Главное меню🔄')),

            '🎲Прочее🎲': RangeNumberReplyButton(['🌤Погода🌤', '😺Котики😺', '🦠COVID-19🦠', '🔄Главное меню🔄']),
        }
        # погодник
        presets = get_default_config()
        presets['language'] = 'ru'
        self.__owm = pyowm.OWM(owm_token, presets)

    def __str__(self):
        return f'Токен:{self.token}'

    def run(self):

        @self.message_handler(commands=['start'])
        def start_message(message):
            db = dbcontrol.DBcontrol()

            if not db.user_exists(message.from_user.id):

                db.add_user(message.from_user.id)
                self.send_message(message.chat.id, subtext.help_message.replace("%name%", message.from_user.first_name),
                                  reply_markup=self.dirs['🔄Главное меню🔄'])
                sleep(0.100)
            else:
                self.send_message(message.chat.id, "Рад видеть вас снова! 🙂")

            db.close()

        @self.message_handler(commands=['ban'])
        def ban_command(message):
            if not dbcontrol.User(message.from_user.id).admin_status:
                self.send_message(message.chat.id, "⛔В доступе отказано!⛔")
                return
            try:

                user_id = str(message.text).split(' ')[1]
                status = str(message.text).split(' ')[2]
                dbcontrol.User(int(user_id)).ban(True if status.lower() == 'true' else False)

                self.send_message(message.chat.id, "✅Успех✅")

            except IndexError:
                self.send_message(message.chat.id, "⛔Прорущен аргумент!⛔")

        @self.message_handler(commands=['db'])
        def dump_db(message):

            if not dbcontrol.User(message.from_user.id).admin_status:
                self.send_message(message.chat.id, "⛔В доступе отказано!⛔")
                return

            try:

                line = str(message.text).split(' ')
                with open(f"data_bases/{line[1]}", 'rb') as f:
                    self.send_document(message.chat.id, f)

            except FileNotFoundError:
                self.send_message(message.chat.id, f'⛔База данных  не была найдена⛔')

            except IndexError:
                self.send_message(message.chat.id, f'⛔Нет аргумента⛔')

        @self.message_handler(commands=['everyone'])
        def everyone(message):
            if not dbcontrol.User(message.from_user.id).admin_status:
                self.send_message(message.chat.id, "⛔В доступе отказано!⛔")
                return

            counter = 0
            db = dbcontrol.DBcontrol()

            try:
                for member in db.get_all_users():
                    try:
                        self.send_message(member[1], message.text[9:], parse_mode='Markdown')
                        counter += 1

                    except Exception:
                        pass
                self.send_message(message.chat.id, f"Выполнено {counter}/{len(db.get_all_users())}")

            except KeyError:
                self.send_message(message.chat.id, f'⛔Нет аргументов⛔')

            finally:
                db.close()

        @self.message_handler(commands=['admin'])
        def set_admin(message):
            if not dbcontrol.User(message.from_user.id).admin_status:
                self.send_message(message.chat.id, "⛔В доступе отказано!⛔")
                return
            try:
                user_id = str(message.text).split(' ')[1]
                status = str(message.text).split(' ')[2]
                dbcontrol.User(int(user_id)).admin(True if status.lower() == 'true' else False)
                self.send_message(message.chat.id, "✅Успех✅")
            except IndexError:
                self.send_message(message.chat.id, "⛔Прорущен аргумент!⛔")

        @self.callback_query_handler(func=lambda call: True)
        def callback_inline(call):

            if call.data == '9':
                self.send_message(call.message.chat.id, 'Теперь выберите Ваш класс. 👇',
                                  reply_markup=RangeNumberInLineButton(self.__nineCharList))

            elif call.data == '10':
                self.send_message(call.message.chat.id, 'Теперь выберите Ваш класс. 👇',
                                  reply_markup=RangeNumberInLineButton(self.__tenCharList))

            elif call.data == '11':
                self.send_message(call.message.chat.id, 'Теперь выберите Ваш класс. 👇',
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

            if dbcontrol.User(message.from_user.id).ban_status:
                self.send_message(message.chat.id, '⛔Ваша запись была заблокированна⛔')

            elif message.text == '📃Расписание📃':
                self.send_message(message.chat.id, 'Пожалуйста, выберите параллель, в которой Вы обучаетесь. 👇',
                                  reply_markup=RangeNumberInLineButton(range(9, 12)))

            elif message.text == '📚Школа📚':
                self.send_message(message.chat.id, 'Вы находитесь в разделе «📚Школа📚».',
                                  reply_markup=self.dirs[message.text])

            elif message.text == '🔄Главное меню🔄':
                self.send_message(message.chat.id, 'Вы вернулись в главное меню.',
                                  reply_markup=self.dirs[message.text])

            elif message.text == '📰Новости📰':
                site = siteparser.News()
                self.send_message(message.chat.id, f'*{site.getLastNewsTitle()}*\n\n{site.getLastNewsText()}',
                                  parse_mode='Markdown')

            elif message.text == '🎲Прочее🎲':
                self.send_message(message.chat.id, 'В находитесь в разделе «🎲Прочее 🎲».',
                                  reply_markup=self.dirs[message.text])

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

            elif message.text == '🦠COVID-19🦠':
                site = siteparser.Covid19()
                self.send_message(message.chat.id, "Минутку...")
                self.send_message(
                    message.chat.id,
                    f"*🦠COVID🦠*\n\n🤒Заболело: *{site.getAllInfected()}* человек.\n"
                    f"😵Умерло: *{site.getAllDied()}* человек.\n"
                    f"😎Вылечилось: *{site.getAllHealed()}* человек.\n"
                    f"🤒Зарозилось за день: *{site.getInfectedInLastDay()}* человек.\n\n"
                    "*Пожалуйста соблюдайте дистанцию и носите маску!*",
                    parse_mode='Markdown')

            elif message.text == '😺Котики😺':
                try:
                    url = requests.get('https://thiscatdoesnotexist.com/')

                    with open(f'{message.chat.id}.jpg', 'wb') as f:
                        f.write(url.content)

                    with open(f'{message.chat.id}.jpg', 'rb') as f:
                        self.send_photo(message.chat.id, f)

                    os.remove(f'{message.chat.id}.jpg')
                except PermissionError:
                    self.send_message(message.chat.id, "⛔Вы отправляете сообщения слишком быстро!⛔")
            elif message.text == '❓Помощь❓':
                self.send_message(message.chat.id, 'Вы перешли в раздел «❓Помощь❓»',
                                  reply_markup=self.dirs[message.text])

            elif message.text == '⚙️Команды⚙️':
                with open('media/text/commands_help.txt', 'r', encoding="utf-8") as f:
                    self.send_message(message.chat.id, f.read(), parse_mode='Markdown')

            elif message.text == '©️GitHub©️':
                with open('media/text/github.txt', 'r', encoding="utf-8") as f:
                    self.send_message(message.chat.id, f.read(), parse_mode='Markdown')

            elif message.text == '💬Контакты💬':
                with open('media/text/contacts.txt', 'r', encoding="utf-8") as f:
                    self.send_message(message.chat.id, f.read(), parse_mode='Markdown')

            elif message.text == '👤Аккаунт👤':
                user = dbcontrol.User(message.from_user.id)
                self.send_message(message.chat.id, f"*ИНФОРМАЦИЯ ОБ АККАУНТЕ*\n\n*ID:* {user.id}\n"
                                                   f"*Дата регистрации:* `{user.reg_date}`\n"
                                                   f"*Права администратора:* {'✅' if user.admin_status else '❌'}\n"
                                                   f"*Блокировка:* {'❌' if not user.ban_status else '⚠'}",
                                  parse_mode='Markdown')

        self.polling()


if __name__ == '__main__':
    Bot(os.environ.get('TOKEN'), os.environ.get('OWN_TOKEN')).run()
