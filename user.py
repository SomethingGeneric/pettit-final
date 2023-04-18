# stdlib
import os

# pip packages
import toml
import bcrypt


# Idea for new_history:
"""
{
    "frame_url": <string>,
    "age": <int>,
    "main_emotion": <string>,
    ....
    # so that we can do a like "def generate_avg_age"
}
"""

# self.cookies
"""
[
    {
        "user": <str>,
        "key": <str>
    },
]
"""


class User:
    def __init__(self, id_str=None, usern=None, passw=None, ihistory=None):
        self.id = id_str
        self.username = usern
        self.passw = passw
        self.history = ihistory if ihistory is not None else []

    def add_to_history(self, new_history):
        self.history.append(new_history)

    def __str__(self):
        all_my_stuff = {
            "id": self.id,
            "username": self.username,
            "password": self.passw,
            "history": self.history,
        }
        return toml.dumps(all_my_stuff)


class UsersDatabase:
    def __init__(self):
        if not os.path.exists("db"):
            os.makedirs("db")
        self.cookies = []

    def expire_cookie(self, user):
        for data in self.cookies:
            if data["user"] == user:
                self.cookies.remove(data)
                return True
        return False

    def set_cookie(self, user, key):
        self.expire_cookie(user)
        self.cookies.append({"user": user, "key": key})

    def check_cookie(self,untrusted):
        for data in self.cookies:
            if data["key"] == untrusted:
                return True
        return False
    
    def get_cookie_thing(self, untrusted):
        for data in self.cookies:
            if data["key"] == untrusted:
                return data
        return None

    def get_id_for_session(self, untrusted):
        data = self.get_cookie_thing(untrusted)
        return self.find_id_by_username(data['user'])

    def commit_user(self, user):
        with open(f"db{os.sep}{user.id}.toml", "w") as f:
            f.write(str(user))

    def load_user(self, user_id):
        fn = f"db{os.sep}{user_id}.toml"
        if os.path.exists(fn):
            stuff = open(fn).read()
            data = toml.loads(stuff)
            new = User(data["id"], data["username"], data["password"], data["history"])
            return new
        else:
            return None

    def find_id_by_username(self, user):
        for f in os.listdir("db"):
            if ".toml" in f:
                stuff = open(f"db{os.sep}{f}").read()
                data = toml.loads(stuff)
                if data["username"] == user:
                    return data["id"]
        return None

    def add_history_to(self, session, new_history):
        obj = self.get_cookie_thing(session)
        username = obj["user"]
        user_id = self.find_id_by_username(username)
        user_object = self.load_user(user_id)
        user_object.add_to_history(new_history)
        self.commit_user(user_object)

    def register_user(self, id, user, passw):

        ptpw = passw

        hashed_pw = bcrypt.hashpw(ptpw, bcrypt.gensalt())

        new = User(id, user, hashed_pw)
        self.commit_user(new)

    def auth_user(self, id, attempt):
        user = self.load_user(id)
        if user:
            return bcrypt.checkpw(attempt, user.passw)
        return False

    def auth_by_user(self, un, attempt):
        id = self.find_id_by_username(un)
        if id:
            return self.auth_user(id, attempt)
        return False


if __name__ == "__main__":
    db = UsersDatabase()
    
    db.register_user("1", "matt", "TestPassword")

    if db.auth_by_user("matt", input("Password for matt: ")):
        print("Woo yea!")
    else:
        print("You failed to auth")