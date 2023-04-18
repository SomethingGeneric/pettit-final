from deepface import DeepFace
from flask import Flask, render_template, request, redirect, url_for, make_response, send_file
import filetype
import os
import io
import base64
from datetime import datetime
from PIL import Image
from urllib.parse import quote

app = Flask(__name__)

if not os.path.exists("frames"):
    os.makedirs("frames")

@app.route('/stream', methods=['POST'])
def lecamera():
    try:
        # Get the frame from the request
        frame = request.json['frame'].replace("data:image/jpeg;base64,","")
        # Save the frame to disk or process it as needed
        img = Image.open(io.BytesIO(base64.decodebytes(bytes(frame, "utf-8"))))
        filename = f"frames/frame-{quote(str(datetime.now()))}.jpg"
        img.save(filename)
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
            filename=filename.replace("frames/",""),
            age=age,
            main_em=main_emotion,
            main_gender=main_gender,
            main_race=main_race,
            s_em=clean_emotions,
            s_gender=likely_genders,
            s_races=likely_races,
        )
    except Exception as e:
        #return render_template("fail.html", fail=str(e))
        print(str(e))
        return f"FAIL: {str(e)}"

@app.route("/")
def camamammamammera():
    return render_template("camera.html")

@app.route("/image/id/<id>")
def secureish(id):
    if os.path.exists(f"frames/{id}"):
        return send_file(f"frames/{id}")
    else:
        return ""

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", debug=True)
    except Exception as e:
        print(str(e))
