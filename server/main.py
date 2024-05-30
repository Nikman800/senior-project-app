

from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
import os
from opencv.fr import FR
from opencv.fr.persons.schemas import PersonBase
from opencv.fr.search.schemas import SearchRequest, SearchMode
from opencv.fr.api_error import APIError
from flask_cors import CORS
from dotenv import load_dotenv

import time
import json

import io

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import storage

import dlib

 # Use the application default credentials.
cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

with open('credentials.json') as f:
    credentials = json.load(f)




# Set up application.
app = Flask(__name__)
app.config['DEBUG'] = True
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

#New function to add the database information to OpenCV
def add_to_opencv(name, storage_client):
    BACKEND_URL = "https://us.opencv.fr"
    DEVELOPER_KEY = os.getenv('DEVELOPER_KEY')

    # Initialize the SDK
    sdk = FR(BACKEND_URL, DEVELOPER_KEY)

    # Get the document with the given name from the Firestore
    doc_ref = db.collection("users").document(name)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()

        # Get the image URL
        image_url = data.get('profile_picture')

        # Check if the image URL is not empty
        if image_url:

            # Download the image from the bucket
            bucket = storage_client.get_bucket('image-storage-senior-project')
            blob = bucket.blob(f"{name}.jpg")
            save_as = f"{name}.jpg"
            blob.download_to_filename(save_as)

            # Check if the person already exists in OpenCV
            try:
                existing_person = sdk.persons.get(name)
            except APIError as e:
                if e.err_code == 'ERR_ENTITY_NOT_FOUND':
                    existing_person = None
                else:
                    raise

            # If the person does not exist, create a new one
            if existing_person is None:
                person = PersonBase([save_as], name)
                person = sdk.persons.create(person)
    else:
        print(f'No such document: {name}')

# Function to scrape a profile from LinkedIn, add to firestore, and add to OpenCV
def scrape_profile(driver, profile_url):
    """Scrape required fields from LinkedIn company URL"""
    driver.get(profile_url)

    profile_name = ''
    profile_title = ''
    profile_location = ''
    about_text = ''
    company_and_title = ''
    date_range = ''
    location = ''
    school_name = ''
    degree_and_field = ''
    dates = ''
    skill_name = ''
    endorsement_count = ''
    image_url = ''
    all_experience_details = []
    all_education_details = []
    all_skill_details = []

    profile_name = driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge").get_attribute("innerText")
    profile_title = driver.find_element(By.CSS_SELECTOR, "div.text-body-medium").get_attribute("innerText")
    profile_location = driver.find_element(By.CSS_SELECTOR, "span.text-body-small.inline").get_attribute("innerText")

    
    time.sleep(2)  # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    #Start of the code to scrape the profile picture
    
    # Locate the profile picture
    profile_pic_element = driver.find_element(By.CSS_SELECTOR, "img.pv-top-card-profile-picture__image--show")
    profile_pic_url = profile_pic_element.get_attribute("src")

    # Download the profile picture
    if profile_pic_url.startswith('http'):
        response = requests.get(profile_pic_url)
        image_name = profile_name + ".jpg"
        with open(image_name, 'wb') as f:
            f.write(response.content)

        # Upload the image to Google Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.get_bucket('image-storage-senior-project')
        blob = bucket.blob(image_name)
        blob.upload_from_filename(image_name)

        # Get the URL of the uploaded image
        image_url = blob.public_url
    else:
        image_url = ""

    #End of the code to scrape the profile picture


    cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "pv-profile-card")))

    # Loop through each card
    for card in cards:
        # Extract card title
        card_title_element = card.find_element(By.CLASS_NAME, "pvs-header__title")
        card_title = card_title_element.text.strip()
        
        print(f"--- {card_title} ---")
        
        # Extract information based on card type
        if card_title == "Activity\nActivity":
            # Extract posts
            posts = card.find_elements(By.CLASS_NAME, "profile-creator-shared-feed-update__mini-container")
            for post in posts:
                # Extract post content
                try:
                    content_element = post.find_element(By.CLASS_NAME, "break-words")  # Target the element with the "break-words" class
                    content = content_element.text.strip()
                except:
                    content = ""

                # Extract author
                try:
                    author_element = post.find_element(By.CLASS_NAME, "feed-mini-update-contextual-description__text")
                    author = author_element.find_element(By.TAG_NAME, "strong").text.strip()
                except:
                    author = ""

                # Extract post date
                try:
                    date_element = post.find_element(By.CLASS_NAME, "feed-mini-update-contextual-description__text")
                    date_text = date_element.text.strip()
                    date_str = date_text.split("•")[-1].strip()  # Assuming date follows "•"
                except:
                    date_str = ""

                # Extract attached article info (if any)
                try:
                    article_element = post.find_element(By.CLASS_NAME, "feed-mini-update-content__single-line-text")
                    article_title = article_element.find_element(By.TAG_NAME, "strong").text.strip()
                    article_source = article_element.find_elements(By.TAG_NAME, "span")[-1].text.strip()
                except:
                    article_title = ""
                    article_source = ""

                # Extract reactions
                try:
                    reaction_element = post.find_element(By.CLASS_NAME, "social-details-social-counts__reactions-count")
                    reactions = int(reaction_element.text.strip())
                except:
                    reactions = 0


        elif card_title == "Experience\nExperience":
            # Find all elements with class 'artdeco-list__item' within the current card
            experience_items = card.find_elements(By.CLASS_NAME, "artdeco-list__item")

            # Initialize an empty list to store all experience details
            # all_experience_details = []

            for experience in experience_items:
                # Initialize a dictionary to store details of this experience item
                experience_details = {}

                # Extract company name and job title (combined)
                try:
                    company_title_element = experience.find_element(By.CLASS_NAME, "t-bold")
                    experience_details['company_and_title'] = company_title_element.text.strip()
                except:
                    experience_details['company_and_title'] = ""

                # Extract date range (adjust the selector if needed)
                try:
                    date_element = experience.find_element(By.CLASS_NAME, "t-14")
                    experience_details['date_range'] = date_element.text.strip()
                except:
                    experience_details['date_range'] = ""

                # Extract location (adjust the selector if needed)
                try:
                    location_element = experience.find_element(By.CLASS_NAME, "t-black--light")
                    experience_details['location'] = location_element.text.strip()
                except:
                    experience_details['location'] = ""

                # Append the details of this experience item to the list
                all_experience_details.append(experience_details)

        elif card_title == "Education\nEducation":
            # Find all list items within the Education card
            education_items = card.find_elements(By.CLASS_NAME, "artdeco-list__item")

            # Initialize an empty list to store all education details
            # all_education_details = []

            for education in education_items:
                # Extract information from within each list item (adjust selectors as needed)

                # Initialize a dictionary to store details of this education item
                education_details = {}
                try:
                    # school_name_element = education.find_element(By.CSS_SELECTOR, "a.optional-action-target-wrapper > div > div > div > span")
                    school_name_element = education.find_element(By.CSS_SELECTOR, "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold > span") 
                    # Assuming the school name is within a 'span' tag inside the element with the given classes
                    # school_name = school_name_element.text.strip()
                    education_details['school_name'] = school_name_element.text.strip()
                except:
                    # school_name = ""
                    education_details['school_name'] = ""
                try:
                    degree_and_field_element = education.find_element(By.CSS_SELECTOR, "span.t-14.t-normal")
                    # degree_and_field = degree_and_field_element.text.strip()
                    education_details['degree_and_field'] = degree_and_field_element.text.strip()
                    # You can further split 'degree_and_field' if needed 
                except:
                    # degree_and_field = ""
                    education_details['degree_and_field'] = ""

                try:
                    dates_element = education.find_element(By.CSS_SELECTOR, "span.t-14.t-black--light > span")
                    education_details['dates'] = dates_element.text.strip()
                    # dates = dates_element.text.strip()
                except:
                    # dates = ""
                    education_details['dates'] = ""

                # Append the details of this education item to the list
                all_education_details.append(education_details)

        elif card_title == "Skills\nSkills":
            # Find all skill container elements
            skill_containers = card.find_elements(By.CLASS_NAME, "artdeco-list__item") 

            # Initialize an empty list to store all skill details
            # all_skill_details = []

            for skill_container in skill_containers:
                # Initialize a dictionary to store details of this skill item
                skill_details = {}

                # Extract skill name 
                try:
                    skill_name_element = skill_container.find_element(By.CSS_SELECTOR, "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold > span")
                    skill_details['skill_name'] = skill_name_element.text.strip() 
                except:
                    skill_details['skill_name'] = ""

                # Extract endorsement count (adjust selector if needed)
                try:
                    endorsement_count_element = skill_container.find_element(By.CLASS_NAME, "t-14") 
                    skill_details['endorsement_count'] = endorsement_count_element.text.strip()
                except:
                    skill_details['endorsement_count'] = ""

                # Append the details of this skill item to the list
                all_skill_details.append(skill_details)

        elif card_title == "Recommendations\nRecommendations":
            # Extract recommendations
            # ... (implement your logic here)
            pass
        elif card_title == "Interests\nInterests":
            # Extract interests (companies and schools)
            # ... (implement your logic here)
            pass
        elif card_title == "About\nAbout":
            try:
                # Locate the element containing the "About" text directly using the class
                about_text_element = card.find_element(By.CLASS_NAME, "inline-show-more-text--is-collapsed") 
                about_text = about_text_element.text.strip()

                # Check for "See More" button
                see_more_button = card.find_element(By.CSS_SELECTOR, "button.inline-show-more-text__button")
                if see_more_button:
                    driver.execute_script("arguments[0].click();", see_more_button)  # Click using JavaScript
                    about_text = about_text_element.text.strip()  # Extract the expanded text

            except:
                pass
                # about_text = ""

    doc_ref = db.collection("users").document(profile_name)
    doc_ref.set({"name": profile_name, "title": profile_title, "location": profile_location, "about": about_text, "experience": all_experience_details, "education": all_education_details, "skills": all_skill_details, "profile_picture": image_url})

    users_ref = db.collection("users")
    docs = users_ref.stream()

    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")

    if image_url:
        add_to_opencv(profile_name, storage_client)
        return f"{profile_name} scraped successfully"
    return f"{profile_name} has no profile picture"

# @app.route("/")
# def homepage():
#     return render_template("homepage.html")

@app.route("/")
def homepage():
    print("Homepage accessed")
    return "Hello, welcome to my homepage!"

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

    # Load face detector from dlib
    detector = dlib.get_frontal_face_detector()

    file = request.files['image']
    img = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = detector(gray)

    output_images = []

    for i, face_rect in enumerate(faces):
        # Extract face coordinates
        x1, y1 = face_rect.left(), face_rect.top()
        x2, y2 = face_rect.right(), face_rect.bottom()
        w, h = x2 - x1, y2 - y1

        # Expand bounding box slightly
        x1 = max(0, int(x1 - 0.2 * w))
        y1 = max(0, int(y1 - 0.2 * h))
        x2 = min(img.shape[1], int(x2 + 0.2 * w))
        y2 = min(img.shape[0], int(y2 + 0.2 * h))

        # Extract and resize face
        face = img[y1:y2, x1:x2]
        min_dim = min(w, h)
        scale = max(200 / min_dim, 1)
        face = cv2.resize(face, (0, 0), fx=scale, fy=scale)

        # Save cropped face
        output_path = f'Output_Images/face_{i}.jpg'
        cv2.imwrite(output_path, face)
        output_images.append(output_path)

    load_dotenv()

    BACKEND_URL = "https://us.opencv.fr"
    DEVELOPER_KEY = os.getenv('DEVELOPER_KEY')
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

    people = []
    print(results)

    for result_dict in results:
        # print(result_dict)
        
        # Check if the dictionary contains a 'person' key within its nested structure
        for key, value in result_dict.items():
            if isinstance(value, dict) and 'person' in value:
                person = value['person']
                name = person['_name']
                # print(f'Name: {name}')

                # Get the document with the given name from the Firestore
                doc_ref = db.collection("users").document(name)
                doc = doc_ref.get()

                if doc.exists:
                    user_data = doc.to_dict()
                    name = user_data.get('name', 'No name field in document')
                    about = user_data.get('about', 'No about field in document')
                    people.append({'name': name, 'about': about})
                else:
                    print(f'No such document: {name}')
            else:
                print(f'No person found in result: {result_dict}')
                
    print(people)
    return jsonify(people)

@app.route('/submit_urls', methods=['POST'])
def scrape_profiles():

    data = request.get_json()
    profileList = data.get('urls', [])  # Get the 'urls' property of the JSON object

    driver = webdriver.Chrome(service=Service(r"C:\chromedriver-win64\chromedriver.exe"))

    # Navigate to LinkedIn login page
    driver.get("https://www.linkedin.com/login")

    # Log in LinkedIn
    username_field = driver.find_element(By.ID, "username")
    username_field.send_keys(credentials['username'])

    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(credentials['password'])

    sign_in_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    sign_in_btn.click()

    results = []

    for profile in profileList:
        results.append(scrape_profile(driver, profile))

    driver.close()
    driver.quit()

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=8000)