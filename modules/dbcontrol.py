import sqlite3
from datetime import datetime


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
            return self.__cursor.execute("INSERT INTO `members` (`account_id`, `reg_date`) VALUES(?, ?)",
                                         (user_id, f"{date.day}.{date.month}.{date.year}"))

    def get_all_users(self):
        with self.__connection:
            return self.__cursor.execute("SELECT * FROM `members`").fetchall()

    def close(self):
        self.__connection.close()


class User:
    def __init__(self, user_id: int):
        self.__connection = sqlite3.connect('data_bases/data.db')
        self.__cursor = self.__connection.cursor()

        with self.__connection:
            data = self.__cursor.execute("SELECT * FROM `members` WHERE `account_id` = ?", (user_id,)).fetchall()[0]

            self.info = {'id': user_id,
                         'ban_status': data[2],
                         'admin_status': data[3],
                         'reg_date': data[4],
                         'class_number': data[5],
                         'class_char': data[6],
                         'sent_messages': data[7]}

    def ban(self, statement: bool = True):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `ban` = ? WHERE `account_id` = ?", (statement,
                                                                                                   self.info['id']))

    def admin(self, statement: bool = True):
        """
        Изменить админ статус
        """
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `admin` = ? WHERE `account_id` = ?", (statement,
                                                                                                     self.info['id']))

    def set_class_number(self, number: int):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `class_number` = ? WHERE `account_id` = ?", (number,
                                                                                                            self.info[
                                                                                                                'id']))

    def set_class_char(self, char: str):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `class_char` = ? WHERE `account_id` = ?",
                                         (char[0].upper(),

                                          self.info['id']))

    def set_sent_messages(self, number: int):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `sent_messages` = ? WHERE `account_id` = ?", (number,
                                                                                                             self.info[
                                                                                                                 'id']))

    def __del__(self):
        self.__connection.close()

    def __str__(self):
        return f"<id={self.info['id']}, ban={self.info['ban_status']}, admin={self.info['admin_status']}>"

    def __repr__(self):
        return f"<id={self.info['id']},ban={self.info['ban_status']}, admin={self.info['admin_status']}>"
