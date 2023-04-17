from deepface import DeepFace
from flask import Flask, render_template, request, redirect, url_for, make_response
import filetype
import os
import io
import base64
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(f"static{os.sep}uploads{os.sep}camera"):
    os.makedirs(f"static{os.sep}uploads{os.sep}camera", exist_ok=True)


@app.route("/")
def index():
    oops = request.cookies.get("OOPSIE", default=None)
    fail = request.cookies.get("FAIL", default=None)

    r = make_response(
        render_template(
            "index.html", warning=oops, fail=fail, uploaded=os.listdir("static/uploads")
        )
    )
    r.delete_cookie("OOPSIE")
    r.delete_cookie("FAIL")
    return r

n = 0

@app.route('/stream', methods=['POST'])
def lecamera():
    try:
        global n
        # Get the frame from the request
        frame = request.json['frame'].replace("data:image/jpeg;base64,","")
        # Save the frame to disk or process it as needed
        img = Image.open(io.BytesIO(base64.decodebytes(bytes(frame, "utf-8"))))
        filename = f"static/uploads/camera/frame-{n}.jpg"
        img.save(filename)
        n += 1
        person = DeepFace.analyze(
            img_path=filename
        )[0]

        age = person["age"]  # normal
        main_emotion = person["dominant_emotion"]  # normal
        main_gender = person["dominant_gender"]  # normal
        main_race = person["dominant_race"]  # normal

        emotions = person["emotion"]  # dict
        sorted_emotions = {
            k: v
            for k, v in sorted(
                emotions.items(), key=lambda item: item[1], reverse=True
            )
        }
        clean_emotions = {}
        for k, v in sorted_emotions.items():
            if "e-" not in str(v):
                clean_emotions[k] = f"{v:.2f}"

        genders = person["gender"]  # dict
        sorted_genders = {
            k: v
            for k, v in sorted(
                genders.items(), key=lambda item: item[1], reverse=True
            )
        }
        likely_genders = {}
        for k, v in sorted_genders.items():
            likely_genders[k] = f"{v:.2f}"

        races = person["race"]  # dict
        sorted_races = {
            k: v
            for k, v in sorted(
                races.items(), key=lambda item: item[1], reverse=True
            )
        }
        likely_races = {}
        for k, v in sorted_races.items():
            if float(str(v).replace("%", "")) > 1.0:
                likely_races[k] = f"{float(str(v).replace('%','')):.2f}"

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
        return render_template("fail.html", fail=str(e))

@app.route("/camera")
def camamammamammera():
    return render_template("camera.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if request.files["file"].filename != "":
            file = request.files["file"]
            filename = file.filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            if not filetype.is_image(os.path.join(app.config["UPLOAD_FOLDER"], filename)):
                resp = make_response(redirect("/"))
                resp.set_cookie("FAIL", "This thing is not an image: " + filename)
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                return resp
            else:
                return redirect(f"/analyze/{filename}")
        else:
            resp = make_response(redirect("/"))
            resp.set_cookie("OOPSIE", "No file provided")
            return resp
    except Exception as e:
       return render_template("fail.html", fail=str(e)) 

@app.route("/analyze/<filename>")
def show_info(filename):
    if not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], filename)):
        resp = make_response(redirect("/"))
        resp.set_cookie("OOPSIE", "Seems like there's no file called: " + filename)
        return resp
    else:
        try:
            person = DeepFace.analyze(
                img_path=os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )[0]

            age = person["age"]  # normal
            main_emotion = person["dominant_emotion"]  # normal
            main_gender = person["dominant_gender"]  # normal
            main_race = person["dominant_race"]  # normal

            emotions = person["emotion"]  # dict
            sorted_emotions = {
                k: v
                for k, v in sorted(
                    emotions.items(), key=lambda item: item[1], reverse=True
                )
            }
            clean_emotions = {}
            for k, v in sorted_emotions.items():
                if "e-" not in str(v):
                    clean_emotions[k] = f"{v:.2f}"

            genders = person["gender"]  # dict
            sorted_genders = {
                k: v
                for k, v in sorted(
                    genders.items(), key=lambda item: item[1], reverse=True
                )
            }
            likely_genders = {}
            for k, v in sorted_genders.items():
                likely_genders[k] = f"{v:.2f}"

            races = person["race"]  # dict
            sorted_races = {
                k: v
                for k, v in sorted(
                    races.items(), key=lambda item: item[1], reverse=True
                )
            }
            likely_races = {}
            for k, v in sorted_races.items():
                if float(str(v).replace("%", "")) > 1.0:
                    likely_races[k] = f"{float(str(v).replace('%','')):.2f}"

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
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return render_template("fail.html", fail=str(e))


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", debug=True)
    except Exception as e:
        print(str(e))
