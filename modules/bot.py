import telebot
from telebot import types
from modules import subtext, siteparser, dbcontrol
import pyowm
import requests
from PIL import Image
import os
from pyowm.utils.config import get_default_config
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

        # разделы
        self.__dirs = {
            '🔄Главное меню🔄': RangeNumberReplyButton(['📚Школа📚', '🎲Прочее🎲', '👤Аккаунт👤', '❓Помощь❓']),

            '👤Аккаунт👤': RangeNumberReplyButton(['📂Информация📂', '🔢Номер класса🔢', '🔡Буква класса🔡',
                                                  '🔄Главное меню🔄']),

            '📚Школа📚': RangeNumberReplyButton(['📃Расписание📃', '📰Новости📰', '🔄Главное меню🔄']),

            '❓Помощь❓': RangeNumberReplyButton(('⚙️Команды⚙️', '💬Контакты💬', '©️GitHub©️',
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
        def start_message(message: types.Message):
            db = dbcontrol.DBcontrol()

            if not db.user_exists(message.from_user.id):

                db.add_user(message.from_user.id)
                self.send_message(message.chat.id, subtext.help_message.replace("%name%", message.from_user.first_name),
                                  reply_markup=self.__dirs['🔄Главное меню🔄'])
                sleep(0.100)
            else:
                self.send_message(message.chat.id, "Рад видеть вас снова! 🙂")

            db.close()

        @self.message_handler(commands=['ban'])
        def ban_command(message: types.Message):
            if not dbcontrol.User(message.from_user.id).info['admin_status']:
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
        def dump_db(message: types.Message):

            if not dbcontrol.User(message.from_user.id).info['admin_status']:
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

        @self.message_handler(commands=['post'])
        def everyone(message: types.Message):
            if not dbcontrol.User(message.from_user.id).info['admin_status']:
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
        def set_admin(message: types.Message):
            if not dbcontrol.User(message.from_user.id).info['admin_status']:
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
        def callback_inline(call: types.CallbackQuery):
            user = dbcontrol.User(call.from_user.id)

            if call.data in ('9', '10', '11'):
                user.set_class_number(int(call.data))
                self.send_message(call.message.chat.id, '✅Изменено✅')

            elif call.data in 'АБВГДЛМИСЭ':
                user.set_class_char(call.data)
                self.send_message(call.message.chat.id, '✅Изменено✅')

            else:
                pass

        @self.message_handler(content_types=['text'])
        def handle_message(message: types.Message):

            if dbcontrol.User(message.from_user.id).info['ban_status']:
                self.send_message(message.chat.id, '⛔Ваша запись была заблокированна⛔')

            elif message.text == '📃Расписание📃':
                user = dbcontrol.User(message.from_user.id)
                try:
                    with open(f'media/images/классы/{user.info["class_number"]}/расписание/{user.info["class_char"]}.jpg', 'rb') as f:
                        self.send_photo(message.chat.id,f )

                except FileNotFoundError:
                    self.send_message(message.chat.id, '😧Расписание для класса '
                                                       f'{user.info["class_number"]}-{user.info["class_char"]} '
                                                       'не было найдено!😧')

            elif message.text == '📚Школа📚':
                self.send_message(message.chat.id, 'Вы находитесь в разделе «📚Школа📚».',
                                  reply_markup=self.__dirs[message.text])

            elif message.text == '🔄Главное меню🔄':
                self.send_message(message.chat.id, 'Вы вернулись в главное меню.',
                                  reply_markup=self.__dirs[message.text])

            elif message.text == '📰Новости📰':
                site = siteparser.News()
                self.send_message(message.chat.id, f'*{site.getLastNewsTitle()}*\n\n{site.getLastNewsText()}',
                                  parse_mode='Markdown')

            elif message.text == '🎲Прочее🎲':
                self.send_message(message.chat.id, 'В находитесь в разделе «🎲Прочее 🎲».',
                                  reply_markup=self.__dirs[message.text])

            elif message.text == '🌤Погода🌤':
                try:
                    mgr = self.__owm.weather_manager()
                    w = mgr.weather_at_place('Москва').weather
                    self.send_message(message.chat.id, "*Погода на сегодня.*\n\n"
                                                       f"*Статус:* {w.detailed_status}\n"
                                                       f"*Температура:* {w.temperature('celsius')['temp']} ℃\n"
                                                       f"*Скорость ветра:* {w.wind()['speed']} м\\с\n"
                                                       f"*Влажность:* {w.humidity}%\n*Облачность:* {w.clouds}%",
                                      parse_mode='Markdown')

                except Exception as e:
                    self.send_message(message.chat.id, f'⛔{e}⛔')

            elif message.text == '🦠COVID-19🦠':
                self.send_message(message.chat.id, "Минутку...")

                information = siteparser.Covid19().getinfo()
                self.send_message(
                    message.chat.id,
                    f"*🦠COVID🦠*\n\n🤒Заболело: *{information['all_infected']}* человек.\n"
                    f"😵Умерло: *{information['all_died']}* человек.\n"
                    f"😎Вылечилось: *{information['all_healed']}* человек.\n"
                    f"🤒Зарозилось за день: *{information['last_infected']}* человек.\n\n"
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
                self.send_message(message.chat.id, f'Вы перешли в раздел «{message.text}»',
                                  reply_markup=self.__dirs[message.text])

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
                self.send_message(message.chat.id, f'Вы перешли в раздел «{message.text}»',
                                  reply_markup=self.__dirs[message.text])

            elif message.text == '📂Информация📂':
                user = dbcontrol.User(message.from_user.id)
                self.send_message(message.chat.id, f"*ИНФОРМАЦИЯ ОБ АККАУНТЕ*\n\n*ID:* {user.info['id']}\n"
                                                   f"*Дата регистрации:* `{user.info['reg_date']}`\n"
                                                   f"*Права администратора:* {'✅' if user.info['admin_status'] else '❌'}\n"
                                                   f"*Блокировка:* {'❌' if not user.info['ban_status'] else '⚠'}\n"
                                                   f"*Класс:* {user.info['class_number']}-{user.info['class_char']}",
                                  parse_mode='Markdown')

            elif message.text == '🔢Номер класса🔢':
                self.send_message(message.chat.id, 'Пожалуйста, выберите параллель.',
                                  reply_markup=RangeNumberInLineButton(range(9, 12)))

            elif message.text == '🔡Буква класса🔡':
                self.send_message(message.chat.id, 'Пожалуйста, выберите параллель.',
                                  reply_markup=RangeNumberInLineButton('АБВГДЛМИСЭ'))


        self.polling()