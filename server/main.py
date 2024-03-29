from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
from opencv.fr import FR
from opencv.fr.persons.schemas import PersonBase
from opencv.fr.search.schemas import SearchRequest, SearchMode
from opencv.fr.api_error import APIError
from flask_cors import CORS

# Set up application.
app = Flask(__name__)
cors = CORS(app, origins='*')

def result_to_dict(result):
    result_dict = {}
    for key, value in result.__dict__.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            result_dict[key] = value
        elif isinstance(value, list):
            result_dict[key] = [result_to_dict(item) if hasattr(item, '__dict__') else item for item in value]
        elif hasattr(value, '__dict__'):
            result_dict[key] = result_to_dict(value)
        else:
            result_dict[key] = str(value)
    return result_dict

# @app.route("/")
# def homepage():
#     return render_template("homepage.html")

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    upload_dir = 'Uploaded_Images'
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    img = cv2.imread(file_path)

    return jsonify({'message': 'Image uploaded and processed successfully'}), 200

@app.route('/detect_faces', methods=['POST'])
def detect_faces():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    file = request.files['image']
    img = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.5, 4)

    output_images = []

    for i, (x, y, w, h) in enumerate(faces):
        x = max(0, int(x - 0.2 * w))
        y = max(0, int(y - 0.2 * h))
        w = min(img.shape[1] - x, int(w + 0.4 * w))
        h = min(img.shape[0] - y, int(h + 0.4 * h))

        face = img[y:y+h, x:x+w]

        min_dim = min(w, h)
        scale = max(200 / min_dim, 1)
        face = cv2.resize(face, (0, 0), fx=scale, fy=scale)

        output_path = f'Output_Images/face_{i}.jpg'

        cv2.imwrite(output_path, face)

        output_images.append(output_path)

    BACKEND_URL = "https://us.opencv.fr"
    DEVELOPER_KEY = "eUGJc-tYzJhNmUxZWEtYTM1ZS00N2JlLTk2MDQtY2I0MDRlNzFjYzRi"
    sdk = FR(BACKEND_URL, DEVELOPER_KEY)

    results = []

    for output_image in output_images:
        try:
            search_request = SearchRequest([output_image])
            results_list = sdk.search.search(search_request)
            for result in results_list:
                result_dict = result_to_dict(result)
                results.append({output_image: result_dict})
        except APIError as e:
            if e.err_code == 'ERR_NO_FACES_FOUND':
                results.append({output_image: 'No faces found. This person could not be found.'})
            else:
                raise

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, port=8080)