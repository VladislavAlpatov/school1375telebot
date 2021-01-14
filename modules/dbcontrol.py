import sqlite3
from datetime import datetime


class DBcontrol:

    def __init__(self):
        self.connection = sqlite3.connect('data_bases/members.db')
        self.cursor = self.connection.cursor()

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `members` WHERE `account_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id: int, ban: bool = False, admin: bool = False):
        with self.connection:
            date = datetime.now()
            return self.cursor.execute("INSERT INTO `members` (`account_id`, `ban`, `admin`, `reg_date`) VALUES(?, ?, ?, ?)",
                                       (user_id,
                                        ban,
                                        admin,
                                        f"{date.day}.{date.month}.{date.year}"))

    def close(self):
        self.connection.close()


class User:
    def __init__(self, user_id: int):

        self.id: int = user_id
        self.__connection = sqlite3.connect('data_bases/members.db')
        self.__cursor = self.__connection.cursor()

        with self.__connection:
            info = self.__cursor.execute("SELECT * FROM `members` WHERE `account_id` = ?", (user_id,)).fetchall()[0]

            self.ban_status: bool = info[2]
            self.admin_status: bool = info[3]

    def ban(self, statement: bool = True):
        with self.__connection:
            return self.__cursor.execute("UPDATE `members` SET `ban` = ? WHERE `account_id` = ?", (statement, self.id))

    def __del__(self):
        self.__connection.close()

    def __str__(self):
        return f"<id={self.id}, ban={self.ban_status}, admin={self.admin_status}>"

    def __repr__(self):
        return f"<id={self.id}, ban={self.ban_status}, admin={self.admin_status}>"
