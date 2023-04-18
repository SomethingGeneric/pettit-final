# Stdlib
import os
import io, random, string
import base64

# Pip Packages
from PIL import Image, ImageDraw
from deepface import DeepFace
from flask import Flask, render_template, request, make_response, redirect

# Custom
from user import UsersDatabase

app = Flask(__name__)
db = UsersDatabase()

if not os.path.exists(f"static{os.sep}frames"):
    os.makedirs(f"static{os.sep}frames", exist_ok=True)


def rndstr():
    letters = string.ascii_letters
    RAND = "".join(random.choice(letters) for i in range(10))
    return RAND

def handle_cookies(request):
    stuff = [request.cookies.get("FAILMSG"), request.cookies.get("WARNMSG"), request.cookies.get("SUCCESSMSG")]
    return stuff


@app.route("/stream/<id>", methods=["POST"])
def lecamera(id):
    session = request.cookies.get('goomba')
    if db.check_cookie(session):
        try:
            # Get the frame from the request
            frame = request.json["frame"].replace("data:image/jpeg;base64,", "")
            # Save the frame to disk or process it as needed
            img = Image.open(io.BytesIO(base64.decodebytes(bytes(frame, "utf-8"))))

            dp = f"static{os.sep}frames{os.sep}{id}"

            if not os.path.exists(dp):
                os.makedirs(dp, exist_ok=True)

            filename = f"static{os.sep}frames{os.sep}{id}{os.sep}frame-{rndstr()}.jpg"

            img.save(filename)
            # print(f"Saved to {filename}")

            person = DeepFace.analyze(img_path=filename)[0]

            # print(person)
            # 'region': {'x': 313, 'y': 220, 'w': 140, 'h': 140}

            x = person['region']['x']
            y = person['region']['y']
            w = person['region']['w']
            h = person['region']['h']

            print(f"From DeepFace: {x}, {y} & {w}, {h}")

            x1 = x
            y1 = y

            x2 = x + w
            y2 = y + h

            print(f"Bounding box: {x1},{y1} & {x2},{y2}")

            image_obj = Image.open(filename)
            draw = ImageDraw.Draw(image_obj)

            draw.rectangle((x1, y1, x2, y2), fill=None, outline=(255,0,0))

            image_obj.save(filename)

            age = person["age"]  # normal
            main_emotion = person["dominant_emotion"]  # normal
            main_gender = person["dominant_gender"]  # normal
            main_race = person["dominant_race"]  # normal

            emotions = person["emotion"]  # dict
            sorted_emotions = {
                k: v
                for k, v in sorted(emotions.items(), key=lambda item: item[1], reverse=True)
            }
            clean_emotions = {}
            for k, v in sorted_emotions.items():
                if "e-" not in str(v):
                    clean_emotions[k] = f"{v:.2f}"

            genders = person["gender"]  # dict
            sorted_genders = {
                k: v
                for k, v in sorted(genders.items(), key=lambda item: item[1], reverse=True)
            }
            likely_genders = {}
            for k, v in sorted_genders.items():
                likely_genders[k] = f"{v:.2f}"

            races = person["race"]  # dict
            sorted_races = {
                k: v
                for k, v in sorted(races.items(), key=lambda item: item[1], reverse=True)
            }
            likely_races = {}
            for k, v in sorted_races.items():
                if float(str(v).replace("%", "")) > 1.0:
                    likely_races[k] = f"{float(str(v).replace('%','')):.2f}"

            all_the_things = {
                "age": age,
                "main_emotion": main_emotion,
                "main_gender": main_gender,
                "main_race": main_race,
                "cleaned_emotions": clean_emotions,
                "likely_genders": likely_genders,
                "likely_races": likely_races
            }

            db.add_history_to(session, all_the_things)

            return render_template(
                "result.html",
                filename=filename,
                age=age,
                main_em=main_emotion,
                main_gender=main_gender,
                main_race=main_race,
                s_em=clean_emotions,
                s_gender=likely_genders,
                s_races=likely_races,
            )
        except Exception as e:
            print("Error: " + str(e))
            return f"FAIL: {str(e)}"
    else:
        return render_template("fail.html", fail=f"<p>Please sign in first. <a href='/'>Go back.</a></p>")

@app.route("/webcam")
def camamammamammera():
    session = request.cookies.get('goomba')
    if db.check_cookie(session):
        return render_template("camera.html", SESSION=db.get_id_for_session(session), username=db.get_cookie_thing(session)["user"])
    else:
        return render_template("fail.html", fail=f"<p>Please sign in first. <a href='/'>Go back.</a></p>")

@app.route("/", methods=['GET', 'POST'])
def indexr():
    if request.method == "GET":
        cookies = handle_cookies(request)
        res = make_response(render_template('index.html', fail=cookies[0], warning=cookies[1], success=cookies[2]))
        for key in ["FAILMSG", "WARNMSG", "SUCCESSMSG"]:
            res.delete_cookie(key)
        return res
    else:
        usern = request.form['usern']
        passw = request.form['passw']

        if db.auth_by_user(usern, passw):
            # woo yea
            resp = make_response(redirect("/webcam"))
            token = rndstr()
            resp.set_cookie("goomba", token)
            db.set_cookie(usern, token)
            return resp
        else:
            return render_template("fail.html", fail=f"<p>Failed to auth for {usern}. <a href='/'>Go back.</a></p>")

@app.route("/register", methods=['GET', 'POST'])
def doreg():
    if request.method == "GET":
        return render_template('register.html')
    else:
        usern = request.form['usern']
        passw = request.form['passw']

        db.register_user(rndstr(), usern, passw)

        res = make_response(redirect("/"))
        res.set_cookie("SUCCESSMSG", "Registed a new user: " + usern)
        return res

if __name__ == "__main__":
    try:
        import webbrowser
        webbrowser.open("http://127.0.0.1:5000")
        app.run(host="0.0.0.0", debug=True)
    except Exception as e:
        print(str(e))
