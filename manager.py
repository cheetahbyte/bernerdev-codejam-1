from http.cookies import SimpleCookie
import sqlite3 as sql
import hashlib as hashy
from uuid import UUID, uuid4
import typing
import os
import datetime
import json
from datetime import datetime as dt

class DatabaseManager():
    def __init__(self) -> None:
        self.database = sql.connect("codejam.db")
        self.cursor = self.database.cursor()
        self.cursor.execute("""create table if not exists `users` (
                            `id` integer not null primary key autoincrement,
                            `created_at` datetime not null default CURRENT_TIMESTAMP,
                            `name` varchar(255) null,
                            `password` varchar(255) null
                            )"""
                            )
        self.database.commit()

    def __enter__(self):
        return self.cursor

    def __exit__(self, x, y, z):
        self.database.commit()
        self.database.close()


class User():
    @staticmethod
    def encrypt(password: str, salt: bytes = os.urandom(32)):
        pwd = hashy.pbkdf2_hmac("sha256", password.encode(
            "utf-8"), salt, 100000, dklen=128)
        return (salt, pwd)

    @staticmethod
    def create(username: str, passwd: str) -> tuple:
        with DatabaseManager() as cursor:
            salt, pwd = User.encrypt(passwd)
            cursor.execute(
                "insert into users (created_at, name, password) values(?,?,?)", (datetime.datetime.now(), username, salt+pwd))
            cursor.execute("select * from users where name = ?", (username,))
            result = cursor.fetchone()
            return result

    @staticmethod
    def check(username: str, passwd: str) -> typing.Union[bool, dict]:
        if User.exists(username):
            index, created, name, hashString = User.get_user(username)
            salt, password = hashString[:32], hashString[32:]
            x, z = User.encrypt(passwd, salt)
            comparaision = x + z
            if comparaision == hashString:
                return True
            else:
                return False
        else:
            return {"error": "user not found"}

    @staticmethod
    def get_user(username: str) -> typing.Tuple[int, datetime.datetime, str, str]:
        with DatabaseManager() as cursor:
            cursor.execute("select * from users where name = ?", (username,))
            data = cursor.fetchone()
        return data

    @staticmethod
    def exists(username: str) -> bool:
        with DatabaseManager() as cursor:
            cursor.execute(
                f"""select * from "users" where name = ?""", (username,))
            result = cursor.fetchone()
            if result != None:
                return True
            return False


class Session:
    @staticmethod
    def data() -> dict:
        with open("sessions.json") as sessionStore:
            data = json.load(sessionStore)
        return data["sessions"]

    @staticmethod
    def add(index: int, username: str) -> None:
        uid = str(uuid4())
        data = Session.data()
        data.append({"index": index, "username": username, "uuid": uid, "validUntil": str(datetime.datetime.now() + datetime.timedelta(minutes=30))})
        x = {}
        x["sessions"] = data
        with open("sessions.json", "w") as sessionStore:
            json.dump(x, sessionStore, indent=4)
        return uid

    @staticmethod
    def remove(index: int, username: str) -> None:
        sessionData: list = Session.data()
        for session in sessionData:
            if session["index"] == index and session["username"] == username:
                sessionData.remove(session)
                break
        x = {}
        x["sessions"] = sessionData
        with open("sessions.json", "w") as sessionStore:
            json.dump(x, sessionStore, indent=4)

    @staticmethod
    def exists(index: int, username: str) -> bool:
        Session.filter()
        sessionData = Session.data()
        for session in sessionData:
            if session["index"] == index and session["username"] == username:
                return True
        return False

    @staticmethod
    def create(index: int, username: str):
        Session.filter()
        if Session.exists(index, username):
            Session.remove(index, username)
            return Session.add(index, username)
        else:
            return Session.add(index, username)

    @staticmethod
    def filter():
        sessions: list = Session.data()
        for session in sessions:
            if datetime.datetime.now() > dt.fromisoformat(session["validUntil"]):
                # expired
                Session.remove(session["index"], session["username"])
            else: 
                pass

    @staticmethod
    def check(cookie: SimpleCookie) -> bool:
        try:
            sessionId: str = cookie["sessionId"].value
            Session.filter()
            data: list = Session.data()
            for session in data:
                if session["uuid"] == sessionId:
                    return True
            return False
        except KeyError:
            return False
    
    @staticmethod
    def find(sessionId: str) -> dict:
        Session.filter()
        data: list = Session.data()
        for session in data:
            if session["uuid"] == sessionId:
                return session
        return None



class Fail2Ban:
    @staticmethod
    def data() -> dict:
        with open("fail2ban.json") as sessionStore:
            data = json.load(sessionStore)
        return data["f2b"]

    @staticmethod
    def fails(ip: str) -> typing.Union[int, None]:
        failers: list = Fail2Ban.data()
        for failer in failers:
            if failer["ip"] == ip:
                return failer["fails"]

    @staticmethod
    def failer(ip: str) -> dict:
        failers: list = Fail2Ban.data()
        for failer in failers:
            if failer["ip"] == ip:
                return failer

    @staticmethod
    def increase(ip: str) -> int:
        if Fail2Ban.fails(ip) is not None:
            failers: list = Fail2Ban.data()
            count: int = Fail2Ban.fails(ip)
            failers.remove({"ip": ip, "fails": count})
            failers.append({"ip": ip, "fails": count + 1})
            x = {}
            x["f2b"] = failers
            with open("fail2ban.json", "w") as failersStore:
                json.dump(x, failersStore, indent=4)
            return count + 1
        else:
            failers: list = Fail2Ban.data()
            failers.append({"ip": ip, "fails": 1})
            x = {}
            x["f2b"] = failers
            with open("fail2ban.json", "w") as failersStore:
                json.dump(x, failersStore, indent=4)
            return 1

    @staticmethod
    def remove(ip: str) -> None:
        if Fail2Ban.fails(ip) is not None:
            failers: list = Fail2Ban.data()
            count: int = Fail2Ban.fails(ip)
            failers.remove({"ip": ip, "fails": count})
            x = {}
            x["f2b"] = failers
            with open("fail2ban.json", "w") as failersStore:
                json.dump(x, failersStore, indent=4)
        else:
            pass
