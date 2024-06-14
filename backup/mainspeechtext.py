import spacy
import os
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from moviepy.editor import ImageSequenceClip
from PIL import Image
from googletrans import Translator

app = Flask(__name__)

# Define your Unsplash API access key
UNSPLASH_ACCESS_KEY = 'w8z8J5TU-1NfjieaG0lIAlpGZ09JLKogSkt3fU3_TH8'

# Directory to save downloaded images
IMAGE_DIR = 'images'

# Default number of images
DEFAULT_NUM_IMAGES = 5

# Function to extract important keywords from the text
def extract_key_points(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    # Extracting key points (nouns) from the text
    key_points = [token.text for token in doc if token.pos_ == "NOUN"]

    return key_points

@app.route('/')
def index():
    return render_template('index.html')

processed_keywords = set()

@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        summarized_text = request.form['summarized_text']
        selected_language = request.form['language']

        # Extract important keywords from the input text
        key_points = extract_key_points(summarized_text)

        # Translate the input text to the selected language
        translator = Translator()
        translated_text = translator.translate(summarized_text, dest=selected_language).text

        # Use the extracted keywords to search for images from the Unsplash API
        for keyword in key_points:
            # Check if the keyword has already been processed
            if keyword not in processed_keywords:
                url = f'https://api.unsplash.com/search/photos/?query={keyword}&client_id={UNSPLASH_ACCESS_KEY}'
                response = requests.get(url)
                data = response.json()
                image_urls = [result['urls']['regular'] for result in data.get('results', [])]

                # Download and save only the first image for each keyword if image_urls is not empty
                if image_urls:
                    if not os.path.exists(IMAGE_DIR):
                        os.makedirs(IMAGE_DIR)
                    
                    image_path = os.path.join(IMAGE_DIR, f'{keyword}_image.jpg')  # Save with a consistent name
                    response = requests.get(image_urls[0])  # Only download the first image
                    with open(image_path, 'wb') as f:
                        f.write(response.content)

                    # Add the keyword to the set of processed keywords
                    processed_keywords.add(keyword)

        # Calculate the duration of each image
        speech_duration = len(translated_text.split()) / 150  # Assuming 150 words per minute
        num_images = len(processed_keywords)
        image_duration = speech_duration / num_images

        # Resize images to the same dimensions
        resized_images = []
        for keyword in processed_keywords:
            img_path = os.path.join(IMAGE_DIR, f'{keyword}_image.jpg')
            img = Image.open(img_path)
            img = img.resize((1280, 720))  # Resize images to 1280x720
            resized_img_path = os.path.join(IMAGE_DIR, f'resized_{keyword}_image.jpg')
            img.save(resized_img_path)
            resized_images.append(resized_img_path)

        # Create list of images paths
        images_list = sorted(resized_images)

        # Create video clip from images
        final_clip = ImageSequenceClip(images_list, fps=0.2)

        # Write the final video to file
        video_path = os.path.join(IMAGE_DIR, 'output_video.mp4')
        final_clip.write_videofile(video_path, codec="libx264", fps=1)

        return jsonify({'video_path': video_path, 'translated_text': translated_text})

@app.route('/images/<path:filename>')
def download_file(filename):
    return send_from_directory(IMAGE_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)





# import requests
# import os
# from flask import Flask, render_template, request, jsonify, send_from_directory
# from moviepy.editor import ImageClip, concatenate_videoclips, CompositeAudioClip, AudioFileClip
# from PIL import Image
# from googletrans import Translator
# import numpy as np

# app = Flask(__name__)

# # Define your Unsplash API access key
# UNSPLASH_ACCESS_KEY = 'w8z8J5TU-1NfjieaG0lIAlpGZ09JLKogSkt3fU3_TH8'

# # Directory to save downloaded images
# IMAGE_DIR = 'images'

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/search', methods=['POST'])
# def search():
#     if request.method == 'POST':
#         summarized_text = request.form['summarized_text']
#         selected_language = request.form['language']

#         # Translate the input text to the selected language
#         translator = Translator()
#         translated_text = translator.translate(summarized_text, dest=selected_language).text

#         # Call Unsplash API to search for images related to the original text
#         url = f'https://api.unsplash.com/search/photos/?query={summarized_text}&client_id={UNSPLASH_ACCESS_KEY}'
#         response = requests.get(url)
#         data = response.json()

#         # Extract image URLs from the response
#         image_urls = [result['urls']['regular'] for result in data.get('results', [])]

#         # Create images directory if it doesn't exist
#         if not os.path.exists(IMAGE_DIR):
#             os.makedirs(IMAGE_DIR)

#         # Download images and save them to the images directory
#         downloaded_images = []
#         for i, url in enumerate(image_urls[:5]):  # Download up to 5 images
#             image_path = os.path.join(IMAGE_DIR, f'image_{i}.jpg')
#             response = requests.get(url)
#             with open(image_path, 'wb') as f:
#                 f.write(response.content)
#             downloaded_images.append(image_path)

#         # Get the speech duration from the translated text
#         speech_duration = len(translated_text.split()) / 150  # Assuming 150 words per minute

#         # Calculate the number of images required based on the speech duration
#         num_images = int(speech_duration) + 1 if speech_duration.is_integer() else int(speech_duration) + 2

#         # Ensure no image is repeated and include more images if the duration is more
#         num_images = min(num_images, len(downloaded_images))

#         # Resize images to the same dimensions
#         resized_images = []
#         for img_path in downloaded_images[:num_images]:
#             img = Image.open(img_path)
#             img = img.resize((1280, 720))  # Resize images to 1280x720
#             resized_img_path = os.path.join(IMAGE_DIR, f'resized_{os.path.basename(img_path)}')
#             img.save(resized_img_path)
#             resized_images.append(resized_img_path)

#         # Create video clips from resized images
#         video_clips = []
#         for img_path in resized_images:
#             clip = ImageClip(img_path).set_duration(speech_duration)
#             video_clips.append(clip)

#         # Concatenate video clips to create the final video
#         final_clip = concatenate_videoclips(video_clips)

#         # Generate speech.mp3 from translated text
#         speech_url = "https://api.elevenlabs.io/v1/text-to-speech/YQfeSHYKoiPl6TIqoU9r"
#         headers = {
#             "Accept": "audio/mpeg",
#             "Content-Type": "application/json",
#             "xi-api-key": "783895cd4d38f6d5ed3ddfd73f2d9732"
#         }
#         speech_data = {
#             "text": translated_text,
#             "voice_settings": {
#                 "stability": 0.5,
#                 "similarity_boost": 0.5
#             },
#             "model_id": "eleven_multilingual_v2"
#         }
#         response = requests.post(speech_url, json=speech_data, headers=headers)
#         with open('speech.mp3', 'wb') as f:
#             f.write(response.content)

#         # Create CompositeAudioClip for the speech
#         speech_clip = CompositeAudioClip([AudioFileClip('speech.mp3')])

#         # Set the audio of the final video to be the speech
#         final_clip = final_clip.set_audio(speech_clip)

#         # Write the final video to file
#         video_path = os.path.join(IMAGE_DIR, 'output_video.mp4')
#         final_clip.write_videofile(video_path, codec="libx264", fps=1)

#         return jsonify({'video_path': video_path, 'translated_text': translated_text})

# @app.route('/images/<path:filename>')
# def download_file(filename):
#     return send_from_directory(IMAGE_DIR, filename, as_attachment=True)

# if __name__ == '__main__':
#     app.run(debug=True)
