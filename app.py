from deepface import DeepFace
from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filename = file.filename
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return redirect(f"/analyze/{filename}")


@app.route("/analyze/<filename>")
def show_info(filename):
    if not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], filename)):
        return "how did we get here?"
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
            return "skill issue: " + str(e)


if __name__ == "__main__":
    app.run(debug=True)
