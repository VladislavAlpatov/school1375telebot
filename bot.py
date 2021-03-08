from aiogram import *
from modules import siteparser, dbcontrol
import pyowm
import requests
import os
from pyowm.utils.config import get_default_config
import asyncio
from fuzzywuzzy import fuzz


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

        # txt файлы
        self.__question_files = ('school_site',
                                 'how_to_connect_to_lesson')
        # погодник
        presets = get_default_config()
        presets['language'] = 'ru'
        self.__owm = pyowm.OWM(owm_token, presets)

        # бот
        self.__dp = Dispatcher(self)
        self.__eventloop = asyncio.get_event_loop()

    @staticmethod
    def __compare(string: str, obj, percent: int):
        """
        Сравнение строк
        """
        for i in obj:
            if fuzz.ratio(string, i) >= percent:
                return True
        return False

    async def __request_banner(self, cool_down: int = 60, max_requests: int = 30):
        while True:
            db = dbcontrol.DBcontrol()
            counter = 0

            for member in db.get_all_users(skip_banned=True):

                if member.info['sent_messages_per_minute'] >= max_requests:
                    member.ban()
                    with open('media/text/help/on_ban_message.txt', encoding='utf-8') as f:
                        await self.send_message(member.info['id'], f.read(), parse_mode='Markdown')

                    counter += 1

                member.set_user_sent_messages_per_minute(0)

            print(f'[BAN-LOG] Выполнена проверка на защиту от DDoS\'а, забанено {counter} записей')

            await asyncio.sleep(cool_down)

    @staticmethod
    async def __web_updater(update_time: int = 60):
        while True:
            print('[WEB-LOG] Обновляю данные...')
            news = siteparser.News()
            covid19 = siteparser.Covid19().getinfo()

            with open('media/text/web/news.txt', 'w') as f:
                f.write(f'*{news.get_last_news_title()}*\n\n{news.get_last_news_text()}')

            with open('media/text/web/covid.txt', 'w', encoding='utf-8') as f:
                f.write(f"*🦠COVID🦠*\n\n🤒Заболело: *{covid19['all_infected']}* человек.\n"
                        f"😵Умерло: *{covid19['all_died']}* человек.\n"
                        f"😎Вылечилось: *{covid19['all_healed']}* человек.\n"
                        f"🤒Заразилось за день: *{covid19['last_infected']}* человек.\n\n"
                        "*Пожалуйста соблюдайте дистанцию и носите маску!*")

            print('[WEB-LOG] Данные успешно обновлены')
            del news, covid19
            await asyncio.sleep(update_time)

    @staticmethod
    def __permissions(admin_only: bool = False, logging: bool = False):
        async def nothing():
            pass

        def dec(func):
            def checker(message: types.Message):
                try:
                    user = dbcontrol.User(message.from_user.id)

                    if admin_only:
                        if user.info['admin_status']:
                            data = func(message)
                        else:
                            data = nothing()

                    elif not user.info['ban_status']:
                        user.set_user_sent_messages_per_minute(user.info['sent_messages_per_minute'] + 1)
                        data = func(message)

                    else:
                        data = nothing()

                    if logging and not user.info['ban_status']:
                        print(f'[CHAT-LOG] <id={message.from_user.id}> '
                              f'<Telegram=@{message.from_user.username}> '
                              f'<user_name={user.info["user_name"]}> '
                              f'<admin={user.info["admin_status"]}> '
                              f'<ban={user.info["ban_status"]}> '
                              f'<text={message.text}> ')
                except IndexError:
                    return nothing()

                return data
            return checker
        return dec

    def run(self):
        @self.__dp.message_handler(commands=['start'])
        async def start_message(message: types.Message):
            db = dbcontrol.DBcontrol()
            if not db.user_exists(message.from_user.id):

                db.add_user(message.from_user.id)

                with open("media/text/help/hello_message.txt", encoding="utf-8") as f:
                    await message.answer(f.read().replace("%name%", message.from_user.first_name),
                                         reply_markup=self.__dirs['🔄Главное меню🔄'], parse_mode='Markdown')
            else:
                await message.answer("Рад видеть вас снова! 🙂", reply_markup=self.__dirs['🔄Главное меню🔄'])

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

                await self.get_chat_member(user_id, user_id)

                user = dbcontrol.User(user_id)
                await message.answer(f"*ПРОСМОТР ПРОФИЛЯ*\n\n"
                                     f"*ИМЯ:* {user.info['user_name']}\n"
                                     f"*ID:* `{user.info['id']}`\n"
                                     f"*КЛАСС:* {user.info['class_number']}-{user.info['class_char']}\n\n"
                                     f"*АДМИН:* {'✅' if user.info['admin_status'] else '❌'}\n"
                                     f"*БЛОКИРОВКА:* {'❌' if not user.info['ban_status'] else '✅'}\n\n"
                                     f"*ЗАРЕГИСТРИРОВАН*: `{user.info['reg_date']}`",
                                     parse_mode='Markdown')

            except IndexError:
                await message.answer("⛔Прорущен аргумент!⛔")

        @self.__dp.message_handler(commands=['db'])
        @self.__permissions(admin_only=True, logging=True)
        async def dump_db(message: types.Message):
            try:

                with open(f"data_bases/{message.text.split(' ')}", 'rb') as f:
                    await message.answer_document(message.chat.id, f)

            except FileNotFoundError:
                await message.answer('⛔База данных  не была найдена⛔')

            except IndexError:
                await message.answer('⛔Нет аргумента⛔')

        @self.__dp.message_handler(commands=['post'])
        @self.__permissions(admin_only=True, logging=True)
        async def post(message: types.Message):
            counter = 0
            db = dbcontrol.DBcontrol()
            members = db.get_all_users(skip_banned=True)

            try:
                await message.answer('⏺Запускаю рассылку⏺')
                for member in members:
                    try:
                        await self.send_message(member.info['id'], message.text[6:], parse_mode='Markdown')
                        counter += 1
                        await asyncio.sleep(0.1)

                    except Exception as e:
                        print(f'[ERROR] {e}')

                await message.answer(f"Выполнено {counter}/{len(members)}")

            except KeyError:
                await message.answer(f'⛔Нет аргументов⛔')

        @self.__dp.message_handler(commands=['set_name'])
        @self.__permissions(logging=True)
        async def set_name(message: types.Message):
            try:
                nick = message.text.split(' ')[1]

                if len(nick) < 15:

                    if dbcontrol.User(message.from_user.id).set_user_name(nick):
                        await message.answer("✅Успех✅")
                    else:
                        await message.answer("⚠Это имя занято⚠")
                else:
                    await message.answer('⚠Это имя очень длинное⚠')

            except IndexError:
                await message.answer("⛔Нет аргумента⛔")

        @self.__dp.message_handler(commands=['admin'])
        @self.__permissions(admin_only=True, logging=True)
        async def set_admin(message: types.Message):
            try:
                dbcontrol.User(int(message.text.split(' ')[1])).admin(
                    True if message.text.split(' ')[2].lower() == 'true' else False)
                await message.answer("✅Успех✅")

            except IndexError:
                await message.answer("⛔Пропущен аргумент!⛔")

        @self.__dp.message_handler(commands=['ask'])
        @self.__permissions(logging=True)
        async def ask_command(message: types.Message):
            text = message.text[4:]

            for file in self.__question_files:
                with open(f'media/text/questions/{file}.txt', encoding='utf-8') as f:
                    if self.__compare(text, f.read().split('\n'), 60):
                        with open(f'media/text/questions/{file}_answer.txt', encoding='utf-8') as f2:
                            await message.answer(f2.read(), parse_mode='Markdown')
                        return
            await message.answer('На ваш вопрос не был найден ответ 😢')

        @self.__dp.message_handler(commands=['set_city'])
        @self.__permissions(logging=True)
        async def set_city_command(message: types.Message):
            try:
                city = message.text[10:]

                if city:
                    dbcontrol.User(message.from_user.id).set_city(city)
                else:
                    await message.answer("⛔Нет аргумента⛔")
            except Exception as e:
                print(e)

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
                    await call.answer('⚠Не удалось загрузить дополнительный материалы⚠')
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
                with open('media/text/web/news.txt', 'r') as f:
                    await message.answer(f.read(), parse_mode='Markdown')

            elif message.text == '🎲Прочее🎲':
                await message.answer('В находитесь в разделе «🎲Прочее🎲».', reply_markup=self.__dirs[message.text])

            elif message.text == '🌤Погода🌤':
                try:
                    city = str(dbcontrol.User(message.from_user.id).info['city'])
                    w = self.__owm.weather_manager().weather_at_place(city).weather

                    await message.answer(f"*Погода в городе \"{city}\"*\n\n"
                                         f"*Статус:* {w.detailed_status}\n"
                                         f"*Температура:* {w.temperature('celsius')['temp']} ℃\n"
                                         f"*Скорость ветра:* {w.wind()['speed']} м\\с\n"
                                         f"*Влажность:* {w.humidity}%\n*Облачность:* {w.clouds}%",
                                         parse_mode='Markdown')

                except Exception as e:
                    await message.answer(f'⛔{e}⛔')

            elif message.text == '🦠COVID-19🦠':
                with open('media/text/web/covid.txt', 'r', encoding='utf-8') as f:
                    await message.answer(f.read(), parse_mode='Markdown')

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
                with open('media/text/help/commands_help.txt', 'r', encoding="utf-8") as f:
                    await message.answer(f.read(), parse_mode='Markdown')

            elif message.text == '©️GitHub©️':
                with open('media/text/help/github.txt', 'r', encoding="utf-8") as f:
                    await message.answer(f.read(), parse_mode='Markdown')

            elif message.text == '💬Контакты💬':
                with open('media/text/help/contacts.txt', 'r', encoding="utf-8") as f:
                    await message.answer(f.read(), parse_mode='Markdown')

            elif message.text == '☝️Цитаты☝️':
                site = siteparser.Quotes()
                await message.answer(f'{site.get_quote_message()}\n\n*{site.get_author()}*', parse_mode="Markdown")

            elif message.text == '👤Аккаунт👤':
                await message.answer(f'Вы перешли в раздел «{message.text}»', reply_markup=self.__dirs[message.text])

            elif message.text == '📂Информация📂':
                user = dbcontrol.User(message.from_user.id)
                await message.answer(f"*ИНФОРМАЦИЯ ОБ АККАУНТЕ*\n\n"
                                     f"*Имя:* {user.info['user_name']}\n"
                                     f"*ID:* {user.info['id']}\n"
                                     f"*Класс:* {user.info['class_number']}-{user.info['class_char']}\n"
                                     f"*Дата регистрации:* `{user.info['reg_date']}`\n"
                                     f"*Город:* {user.info['city']}\n"
                                     f"*Права администратора:* {'✅' if user.info['admin_status'] else '❌'}\n"
                                     f"*Блокировка:* {'❌' if not user.info['ban_status'] else '⚠'}\n",
                                     parse_mode='Markdown')

            elif message.text == '🔢Номер класса🔢':
                await message.answer('Выберите класс', reply_markup=RangeNumberInLineButton(range(9, 12)))

            elif message.text == '📘Доп материалы📘':
                await message.answer("👇Выберите предмет👇", reply_markup=RangeNumberInLineButton(self.__subjects))

            elif message.text == '🔡Буква класса🔡':
                await message.answer('Выберите  букву класса', reply_markup=RangeNumberInLineButton('АБВГДЛМИСЭ'))

        self.__eventloop.create_task(self.__request_banner(10, 10))
        self.__eventloop.create_task(self.__web_updater(360))

        executor.start_polling(self.__dp, skip_updates=True)
