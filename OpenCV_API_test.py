from flask import Flask, request, jsonify
import cv2
import os
from opencv.fr import FR
from opencv.fr.persons.schemas import PersonBase
from opencv.fr.search.schemas import SearchRequest, SearchMode
from opencv.fr.api_error import APIError
import numpy as np

app = Flask(__name__)

@app.route('/detect_faces', methods=['POST'])
def detect_faces():
    print("detect_faces function was called")
    # Load the Haar cascade xml file for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Load the image from the request
    file = request.files['image']
    img = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    # Convert color style from BGR to RGB
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Perform face detection
    faces = face_cascade.detectMultiScale(gray, 1.5, 4)

    # Prepare a list to store the paths of the output images
    output_images = []

    # Loop over all detected faces
    for i, (x, y, w, h) in enumerate(faces):
        # Expand the bounding box by 20% to include some context around the face
        x = max(0, int(x - 0.2 * w))
        y = max(0, int(y - 0.2 * h))
        w = min(img.shape[1] - x, int(w + 0.4 * w))
        h = min(img.shape[0] - y, int(h + 0.4 * h))

        # Extract each face
        face = img[y:y+h, x:x+w]

        # Resize the face to ensure the smallest dimension is at least 200 pixels, preserving aspect ratio
        min_dim = min(w, h)
        scale = max(200 / min_dim, 1)
        face = cv2.resize(face, (0, 0), fx=scale, fy=scale)

        # Define the output path
        output_path = f'Output_Images/face_{i}.jpg'

        # Save each face to a file
        cv2.imwrite(output_path, face)

        # Add the output path to the list
        output_images.append(output_path)

    # Initialize the FR SDK
    BACKEND_URL = "https://us.opencv.fr"
    DEVELOPER_KEY = "eUGJc-tYzJhNmUxZWEtYTM1ZS00N2JlLTk2MDQtY2I0MDRlNzFjYzRi"
    sdk = FR(BACKEND_URL, DEVELOPER_KEY)

    # Define the reference images
    person = PersonBase(
        [
            "Reference_Images/Dev_Sisodia.jpeg",
            "Reference_Images/Dev_Sisodia1.jpeg",
            "Reference_Images/Aaron_Keen.jpg",
        ]
    )

    results = []

    # Create a search request for each output image
    for output_image in output_images:
        try:
            search_request = SearchRequest([output_image])
            result = sdk.search.search(search_request)
            results.append({output_image: result})
        except APIError as e:
            if e.err_code == 'ERR_NO_FACES_FOUND':
                results.append({output_image: 'No faces found. This person could not be found.'})
            else:
                raise

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)