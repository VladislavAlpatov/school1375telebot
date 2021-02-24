from datetime import datetime
import sqlite3


class User:
    def __init__(self, user_id: int):
        self.__connection = sqlite3.connect('data_bases/data.db')
        self.__cursor = self.__connection.cursor()

        with self.__connection:
            data = self.__cursor.execute("SELECT * FROM `members` WHERE `account_id` = ?", (user_id,)).fetchall()[0]

            self.info = {'id': user_id,
                         'user_name': data[1],
                         'ban_status': data[2],
                         'admin_status': data[3],
                         'reg_date': data[4],
                         'class_number': data[5],
                         'class_char': data[6],
                         'sent_messages_per_minute': data[7]}

    def ban(self, statement: bool = True):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `ban` = ? WHERE `account_id` = ?",
                                         (statement, self.info['id']))

    def admin(self, statement: bool = True):
        """
        Изменить админ статус
        """
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `admin` = ? WHERE `account_id` = ?",
                                         (statement, self.info['id']))

    def set_class_number(self, number: int):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `class_number` = ? WHERE `account_id` = ?",
                                         (number, self.info['id']))

    def set_class_char(self, char: str):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `class_char` = ? WHERE `account_id` = ?",
                                         (char[0].upper(), self.info['id']))

    def set_sent_messages(self, number: int):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `sent_messages` = ? WHERE `account_id` = ?",
                                         (number, self.info['id']))

    def set_user_name(self, name: str):
        with self.__connection:
            try:
                return self.__cursor.execute('UPDATE `members` SET `user_name` = ? WHERE `account_id` = ?',
                                             (name, self.info['id']))
            except sqlite3.IntegrityError:
                return False

    def set_user_sent_messages_per_minute(self, number: int):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `sent_messages_per_minute` = ? WHERE `account_id` = ?",
                                         (number, self.info['id']))

    def __del__(self):
        self.__connection.close()

    def __str__(self):
        return f"<id={self.info['id']}, ban={self.info['ban_status']}, admin={self.info['admin_status']}>"

    def __repr__(self):
        return f"<id={self.info['id']},ban={self.info['ban_status']}, admin={self.info['admin_status']}>"


class DBcontrol:

    def __init__(self):
        self.__connection = sqlite3.connect('data_bases/data.db')
        self.__cursor = self.__connection.cursor()

    def user_exists(self, user_id: int):
        with self.__connection:
            result = self.__cursor.execute('SELECT * FROM `members` WHERE `account_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id: int):
        with self.__connection:
            date = datetime.now()
            return self.__cursor.execute("INSERT INTO `members` (`account_id`, `reg_date`, `user_name`) VALUES(?,?,?)",
                                         (user_id, f"{date.day}.{date.month}.{date.year}", user_id))

    def get_all_users(self, skip_banned: bool = False):
        users = []

        with self.__connection:

            if skip_banned:
                data = self.__cursor.execute("SELECT `account_id` FROM `members` WHERE NOT `ban`").fetchall()
            else:
                data = self.__cursor.execute("SELECT `account_id` FROM `members`").fetchall()

            for member_id in data:
                users.append(User(member_id[0]))

        return users

    def get_user_id_by_name(self, name: str) -> int:
        try:
            with self.__connection:
                return self.__cursor.execute("SELECT `account_id` FROM `members` WHERE `user_name` = ?",
                                             (name,)).fetchall()[0][0]
        except IndexError:
            return 0

    def __del__(self):
        self.__connection.close()
