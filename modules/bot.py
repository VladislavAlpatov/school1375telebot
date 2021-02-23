from aiogram import *
from modules import siteparser, dbcontrol
import pyowm
import requests
import os
from pyowm.utils.config import get_default_config
import asyncio


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


class SchoolBot(Bot):
    """
    Основной класс бота
    """

    def __init__(self, token: str, owm_token: str):
        super().__init__(token)

        # разделы
        self.__dirs = {
            '🔄Главное меню🔄': RangeNumberReplyButton(['📚Школа📚', '🎲Прочее🎲', '👤Аккаунт👤', '❓Помощь❓']),

            '👤Аккаунт👤': RangeNumberReplyButton(
                ['📂Информация📂', '🔢Номер класса🔢', '🔡Буква класса🔡', '🔄Главное меню🔄']),

            '📚Школа📚': RangeNumberReplyButton(
                ['📃Расписание📃', '📰Новости📰', '📘Доп материалы📘', '🔄Главное меню🔄']),

            '❓Помощь❓': RangeNumberReplyButton(('⚙️Команды⚙️', '💬Контакты💬', '©️GitHub©️',
                                                '🔄Главное меню🔄')),

            '🎲Прочее🎲': RangeNumberReplyButton(
                ['🌤Погода🌤', '😺Котики😺', '☝️Цитаты☝️', '🦠COVID-19🦠', '🔄Главное меню🔄']),
        }
        self.__subjects = ('Физика', 'Алгебра', 'Русский язык', 'Информатика')

        # погодник
        presets = get_default_config()
        presets['language'] = 'ru'
        self.__owm = pyowm.OWM(owm_token, presets)
        self.__dp = Dispatcher(self)
        self.__eventloop = asyncio.get_event_loop()

    @staticmethod
    def __permissions(admin_only: bool = False, logging: bool = False):
        async def nothing(): pass

        def dec(func):
            def checker(message: types.Message):
                user = dbcontrol.User(message.from_user.id)
                user.set_sent_messages(user.info['sent_messages'] + 1)

                if admin_only:
                    if user.info['admin_status']:
                        data = func(message)
                    else:
                        data = nothing()

                elif not user.info['ban_status']:
                    data = func(message)
                else:
                    data = nothing()

                if logging:
                    print(f'[LOG] <id={message.from_user.id}> '
                          f'<Telegram=@{message.from_user.username}> '
                          f'<user_name={user.info["user_name"]}> '
                          f'<admin={user.info["admin_status"]}> '
                          f'<ban={user.info["ban_status"]}> '
                          f'<text={message.text}> ')

                return data
            return checker
        return dec

    def run(self):
        @self.__dp.message_handler(commands=['start'])
        async def start_message(message: types.Message):
            db = dbcontrol.DBcontrol()
            if not db.user_exists(message.from_user.id):

                db.add_user(message.from_user.id)

                with open("media/text/hello_message.txt", encoding="utf-8") as f:
                    await message.answer(f.read().replace("%name%", message.from_user.first_name),
                                         reply_markup=self.__dirs['🔄Главное меню🔄'])
            else:
                await message.answer("Рад видеть вас снова! 🙂", reply_markup=self.__dirs['🔄Главное меню🔄'])

            db.close()

        @self.__dp.message_handler(commands=['ban'])
        @self.__permissions(admin_only=True, logging=True)
        async def ban_command(message: types.Message):
            try:

                user_id = message.text.split(' ')[1]
                status = message.text.split(' ')[2]
                dbcontrol.User(int(user_id)).ban(True if status.lower() == 'true' else False)

                await message.answer("✅Успех✅")

            except IndexError:
                await message.answer("⛔Прорущен аргумент!⛔")

        @self.__dp.message_handler(commands=['find'])
        @self.__permissions(logging=True)
        async def find_command(message: types.Message):
            db = dbcontrol.DBcontrol()
            try:
                user_id = db.get_user_id_by_name(message.text.split(' ')[1])

                if not user_id:
                    await message.answer("⛔Пользователь не найден!⛔")
                    return

                user = dbcontrol.User(user_id)
                await message.answer(f"*ПРОСМОТР ПРОФИЛЯ*\n\n"
                                     f"*ТEЛЕГРАМ:* @{message.from_user.username}\n"
                                     f"*ID:* {user.info['id']}\n"
                                     f"*АДМИН:* {'✅' if user.info['admin_status'] else '❌'}\n"
                                     f"*КЛАСС:* {user.info['class_number']}-{user.info['class_char']}\n"
                                     f"*БЛОКИРОВКА:* {'❌' if not user.info['ban_status'] else '⚠'}\n"
                                     f"*ЗАРЕГИСТРИРОВАН*: `{user.info['reg_date']}`\n"
                                     f"*ОТПРАВИЛ СООБЩЕНИЙ:* {user.info['sent_messages']}",
                                     parse_mode='Markdown')

            except IndexError:
                await message.answer("⛔Прорущен аргумент!⛔")

            finally:
                db.close()

        @self.__dp.message_handler(commands=['db'])
        @self.__permissions(admin_only=True, logging=True)
        async def dump_db(message: types.Message):
            try:

                line = message.text.split(' ')
                with open(f"data_bases/{line[1]}", 'rb') as f:
                    await message.answer_document(message.chat.id, f)

            except FileNotFoundError:
                await message.answer('⛔База данных  не была найдена⛔')

            except IndexError:
                await message.answer(f'⛔Нет аргумента⛔')

        @self.__dp.message_handler(commands=['post'])
        @self.__permissions(admin_only=True, logging=True)
        async def post(message: types.Message):

            counter = 0
            db = dbcontrol.DBcontrol()

            try:
                await message.answer('⏺Полезная загрузка начата...⏺')
                for member in db.get_all_users():
                    try:

                        await self.send_message(member[1], message.text[6:], parse_mode='Markdown')
                        counter += 1
                        await asyncio.sleep(0.1)

                    except Exception as e:
                        print(f'[ERROR] {e}')

                await message.answer(f"Выполнено {counter}/{len(db.get_all_users())}")

            except KeyError:
                await message.answer(f'⛔Нет аргументов⛔')

            finally:
                db.close()

        @self.__dp.message_handler(commands=['admin'])
        @self.__permissions(admin_only=True, logging=True)
        async def set_admin(message: types.Message):
            try:
                dbcontrol.User(int(message.text.split(' ')[1])).admin(
                    True if message.text.split(' ')[2].lower() == 'true' else False)
                await message.answer("✅Успех✅")

            except IndexError:
                await message.answer("⛔Пропущен аргумент!⛔")

        @self.__dp.callback_query_handler()
        async def callback_inline(call: types.CallbackQuery):
            user = dbcontrol.User(call.from_user.id)

            if call.data in ('9', '10', '11'):
                user.set_class_number(int(call.data))
                await call.answer('✅Изменено✅')

            elif call.data in 'АБВГДЛМИСЭ':
                user.set_class_char(call.data)
                await call.answer('✅Изменено✅')

            elif call.data in self.__subjects:
                try:
                    await call.answer('📶Загружаю📶')
                    with open(f'media/files/классы/{user.info["class_number"]}/доп материалы/{call.data.lower()}/'
                              f'{call.data.lower()}.zip', 'rb') as f:
                        await self.send_document(call.from_user.id, f)

                except FileNotFoundError:
                    await call.answer("😓Файл не найден😓")

                except ConnectionError:
                    await call.answer('⚠️Не удалось загрузить дополнительный материалы⚠️')
            else:
                pass

        @self.__dp.message_handler(content_types=['text'])
        @self.__permissions(logging=True)
        async def handle_message(message: types.Message):

            if message.text == '📃Расписание📃':
                user = dbcontrol.User(message.from_user.id)
                try:
                    with open(
                            f'media/files/классы/{user.info["class_number"]}/расписание/{user.info["class_char"]}.jpg',
                            'rb') as f:
                        await message.answer_photo(f)

                except FileNotFoundError:
                    await message.answer('😧Расписание для класса'
                                         f' {user.info["class_number"]}-{user.info["class_char"]} не было найдено!😧')

            elif message.text == '📚Школа📚':
                await message.answer('Вы находитесь в разделе «📚Школа📚».', reply_markup=self.__dirs[message.text])

            elif message.text == '🔄Главное меню🔄':
                await message.answer('Вы вернулись в главное меню.', reply_markup=self.__dirs[message.text])

            elif message.text == '📰Новости📰':
                site = siteparser.News()
                await message.answer(f'*{site.get_last_news_title()}*\n\n{site.get_last_news_text()}',
                                     parse_mode='Markdown')

            elif message.text == '🎲Прочее🎲':
                await message.answer('В находитесь в разделе «🎲Прочее🎲».', reply_markup=self.__dirs[message.text])

            elif message.text == '🌤Погода🌤':
                try:
                    w = self.__owm.weather_manager().weather_at_place('Москва').weather
                    await message.answer("*Погода на сегодня.*\n\n"
                                         f"*Статус:* {w.detailed_status}\n"
                                         f"*Температура:* {w.temperature('celsius')['temp']} ℃\n"
                                         f"*Скорость ветра:* {w.wind()['speed']} м\\с\n"
                                         f"*Влажность:* {w.humidity}%\n*Облачность:* {w.clouds}%",
                                         parse_mode='Markdown')

                except Exception as e:
                    await message.answer(f'⛔{e}⛔')

            elif message.text == '🦠COVID-19🦠':
                await message.answer("Минутку...")

                information = siteparser.Covid19().getinfo()
                await message.answer(
                    f"*🦠COVID🦠*\n\n🤒Заболело: *{information['all_infected']}* человек.\n"
                    f"😵Умерло: *{information['all_died']}* человек.\n"
                    f"😎Вылечилось: *{information['all_healed']}* человек.\n"
                    f"🤒Заразилось за день: *{information['last_infected']}* человек.\n\n"
                    "*Пожалуйста соблюдайте дистанцию и носите маску!*",
                    parse_mode='Markdown')

            elif message.text == '😺Котики😺':
                try:

                    with open(f'{message.chat.id}.jpg', 'wb') as f:
                        f.write(requests.get('https://thiscatdoesnotexist.com/').content)

                    with open(f'{message.chat.id}.jpg', 'rb') as f:
                        await message.answer_photo(f)

                    os.remove(f'{message.chat.id}.jpg')
                except PermissionError:
                    await message.answer("⛔Вы отправляете сообщения слишком быстро!⛔")

            elif message.text == '❓Помощь❓':
                await message.answer(f'Вы перешли в раздел «{message.text}»', reply_markup=self.__dirs[message.text])

            elif message.text == '⚙️Команды⚙️':
                with open('media/text/commands_help.txt', 'r', encoding="utf-8") as f:
                    await message.answer(f.read(), parse_mode='Markdown')

            elif message.text == '©️GitHub©️':
                with open('media/text/github.txt', 'r', encoding="utf-8") as f:
                    await message.answer(f.read(), parse_mode='Markdown')

            elif message.text == '💬Контакты💬':
                with open('media/text/contacts.txt', 'r', encoding="utf-8") as f:
                    await message.answer(f.read(), parse_mode='Markdown')

            elif message.text == '☝️Цитаты☝️':
                site = siteparser.Quotes()
                await message.answer(f'{site.get_quote_message()}\n\n*{site.get_author()}*', parse_mode="Markdown")

            elif message.text == '👤Аккаунт👤':
                await message.answer(f'Вы перешли в раздел «{message.text}»', reply_markup=self.__dirs[message.text])

            elif message.text == '📂Информация📂':
                user = dbcontrol.User(message.from_user.id)
                await message.answer(f"*ИНФОРМАЦИЯ ОБ АККАУНТЕ*\n\n"
                                     f"*ID:* {user.info['id']}\n"
                                     f"*Дата регистрации:* `{user.info['reg_date']}`\n"
                                     f"*Имя:* {user.info['user_name']}\n"
                                     f"*Права администратора:* {'✅' if user.info['admin_status'] else '❌'}\n"
                                     f"*Блокировка:* {'❌' if not user.info['ban_status'] else '⚠'}\n"
                                     f"*Класс:* {user.info['class_number']}-{user.info['class_char']}\n"
                                     f"*Отправленно сообщений:* {user.info['sent_messages']}", parse_mode='Markdown')

            elif message.text == '🔢Номер класса🔢':
                await message.answer('Выберите класс', reply_markup=RangeNumberInLineButton(range(9, 12)))

            elif message.text == '📘Доп материалы📘':
                await message.answer("👇Выберите предмет👇", reply_markup=RangeNumberInLineButton(self.__subjects))

            elif message.text == '🔡Буква класса🔡':
                await message.answer('Выберите  букву класса', reply_markup=RangeNumberInLineButton('АБВГДЛМИСЭ'))

        # self.__eventloop.create_task(self.pol())

        executor.start_polling(self.__dp, skip_updates=True)
