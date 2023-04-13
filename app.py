from deepface import DeepFace
from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect(f"/analyze/{filename}")

@app.route("/analyze/<filename>")
def show_info(filename):
    if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return "how did we get here?"
    else:
        try:
            face_analysis = DeepFace.analyze(img_path=os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print(face_analysis)
            return render_template('result.html', filename=filename, person=face_analysis[0])
        except Exception as e:
            return "skill issue: " + str(e)

if __name__ == '__main__':
    app.run(debug=True)
