import sqlite3


class DBcontrol:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def get_user_ban_status(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `bans` WHERE `user_id` = ?", (user_id,)).fetchall()

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `bans` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id, name, isban=False):
        with self.connection:
            return self.cursor.execute("INSERT INTO `bans` (`user_id`, `isban`, `name`) VALUES(?,?,?)", (user_id, isban, name))

    def set_ban_status(self, user_id, status):
        with self.connection:
            return self.cursor.execute("UPDATE `bans` SET `isban` = ? WHERE `user_id` = ?", (status, user_id))

    def close(self):
        self.connection.close()
