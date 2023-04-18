# stdlib
import os

# pip packages
import toml
import bcrypt
from flask import render_template

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

    def check_cookie(self, untrusted):
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
        return self.find_id_by_username(data["user"])

    def get_user_for_session(self, untrusted):
        data = self.get_cookie_thing(untrusted)
        return data["user"]

    def commit_user(self, user):
        with open(f"db{os.sep}{user.id}.toml", "w") as f:
            f.write(str(user))

    def load_user(self, user_id):
        fn = f"db{os.sep}{user_id}.toml"
        if os.path.exists(fn):
            stuff = open(fn).read()
            data = toml.loads(stuff)

            uid = None
            username = None
            password = None
            history = None

            if "id" in data.keys():
                uid = data["id"]

            if "username" in data.keys():
                username = data["username"]

            if "password" in data.keys():
                password = data["password"]

            if "history" in data.keys():
                history = data["history"]

            new = User(uid, username, password, history)
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

    # Idea for history objects
    """
    all_the_things = {
        "age": age,
        "main_emotion": main_emotion,
        "main_gender": main_gender,
        "main_race": main_race,
        "cleaned_emotions": clean_emotions, # dict
        "likely_genders": likely_genders, # dict
        "likely_races": likely_races, # dict,
        "filename": filename,
    }
    """

    def do_trends_for(self, username):
        user_obj = self.load_user(self.find_id_by_username(username))

        ages_tally = {}
        all_ages = []  # special since average age is cool imo

        tally_emotions = {}

        tally_genders = {}

        tally_races = {}

        # here #

        all_cleaned_emotions = []

        all_likely_genders = []

        all_likely_races = []

        history_html = ""

        for history in user_obj.history:
            age = history["age"]
            if age in ages_tally.keys():
                ages_tally[age] += 1
            else:
                ages_tally[age] = 1
            all_ages.append(age)

            emotion = history["main_emotion"]
            if emotion in tally_emotions.keys():
                tally_emotions[emotion] += 1
            else:
                tally_emotions[emotion] = 1

            gender = history["main_gender"]
            if gender in tally_genders.keys():
                tally_genders[gender] += 1
            else:
                tally_genders[gender] = 1

            race = history["main_race"]
            if race in tally_races.keys():
                tally_races[race] += 1
            else:
                tally_races[race] = 1

            ##### not using the below for now ######
            all_cleaned_emotions.append(history["cleaned_emotions"])
            all_likely_genders.append(history["likely_genders"])
            all_likely_races.append(history["likely_races"])

            history_html += (
                render_template(
                    "result.html",
                    filename=history["filename"],
                    age=history["age"],
                    main_em=history["main_emotion"],
                    main_gender=history["main_gender"],
                    main_race=history["main_race"],
                    s_em=history["cleaned_emotions"],
                    s_gender=history["likely_genders"],
                    s_races=history["likely_races"],
                ) + "<hr/>"
            )

        final_html = render_template(
            "trends.html",
            username=username,
            history=render_template(
                "trends_list.html",
                ages_tally=ages_tally,
                avg_age=sum(all_ages) / len(all_ages),
                tally_emotions=tally_emotions,
                tally_genders=tally_genders,
                tally_races=tally_races,
            )
            + "<hr/><h3>Previous frames</h3>"
            + history_html,
        )

        return final_html


if __name__ == "__main__":
    db = UsersDatabase()

    db.register_user("1", "matt", "TestPassword")

    if db.auth_by_user("matt", input("Password for matt: ")):
        print("Woo yea!")
    else:
        print("You failed to auth")
