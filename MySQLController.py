import MySQLdb

class MySQLController:
    def __init__(self, hostname, username, password, database):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database = database

    def connect(self):
        self.db = MySQLdb.connect(host=self.hostname, user=self.username, passwd=self.password, db=self.database)
        self.cursor = self.db.cursor()

    def execute(self, query, param=None):
        self.cursor.execute(query, param)

    def commit(self):
        self.db.commit()

    def rowcount(self):
        return self.cursor.rowcount

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.db.close()