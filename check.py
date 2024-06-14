  


import requests
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from moviepy.editor import ImageClip, concatenate_videoclips, CompositeAudioClip, AudioFileClip
from PIL import Image
from googletrans import Translator

app = Flask(__name__)

# Define your Unsplash API access key
UNSPLASH_ACCESS_KEY = 'w8z8J5TU-1NfjieaG0lIAlpGZ09JLKogSkt3fU3_TH8'

# Directory to save downloaded images
IMAGE_DIR = 'images'

# Default number of images
DEFAULT_NUM_IMAGES = 5

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        summarized_text = request.form['summarized_text']
        selected_language = request.form['language']

        # Translate the input text to the selected language
        translator = Translator()
        translated_text = translator.translate(summarized_text, dest=selected_language).text

        # Call Unsplash API to search for images related to the original text
        url = f'https://api.unsplash.com/search/photos/?query={summarized_text}&client_id={UNSPLASH_ACCESS_KEY}'
        response = requests.get(url)
        data = response.json()

        # Extract image URLs from the response
        image_urls = [result['urls']['regular'] for result in data.get('results', [])]

        # Create images directory if it doesn't exist
        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)

        # Download images and save them to the images directory
        downloaded_images = []
        for i, url in enumerate(image_urls[:DEFAULT_NUM_IMAGES]):  # Download up to DEFAULT_NUM_IMAGES images
            image_path = os.path.join(IMAGE_DIR, f'image_{i}.jpg')
            response = requests.get(url)
            with open(image_path, 'wb') as f:
                f.write(response.content)
            downloaded_images.append(image_path)

        # Get the speech duration from the translated text
        speech_duration = len(translated_text.split()) / 150  # Assuming 150 words per minute

        # Adjust the number of images if speech duration exceeds 1 minute
        if speech_duration > 1:
            num_additional_images = int(speech_duration) - 1
            for i in range(DEFAULT_NUM_IMAGES, DEFAULT_NUM_IMAGES + num_additional_images):
                image_path = os.path.join(IMAGE_DIR, f'image_{i}.jpg')
                response = requests.get(image_urls[i])
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                downloaded_images.append(image_path)

        # Calculate the duration of each image
        num_images = len(downloaded_images)
        image_duration = speech_duration / num_images

        # Resize images to the same dimensions
        resized_images = []
        for img_path in downloaded_images:
            img = Image.open(img_path)
            img = img.resize((1280, 720))  # Resize images to 1280x720
            resized_img_path = os.path.join(IMAGE_DIR, f'resized_{os.path.basename(img_path)}')
            img.save(resized_img_path)
            resized_images.append(resized_img_path)

        # Create video clips from resized images
        video_clips = []
        for img_path in resized_images:
            clip = ImageClip(img_path).set_duration(image_duration)
            video_clips.append(clip)

        # Concatenate video clips to create the final video
        final_clip = concatenate_videoclips(video_clips)

        # Generate speech.mp3 from translated text
        speech_url = "https://api.elevenlabs.io/v1/text-to-speech/YQfeSHYKoiPl6TIqoU9r"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": "783895cd4d38f6d5ed3ddfd73f2d9732"
        }
        speech_data = {
            "text": translated_text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            },
            "model_id": "eleven_multilingual_v2"
        }
        response = requests.post(speech_url, json=speech_data, headers=headers)
        with open('speech.mp3', 'wb') as f:
            f.write(response.content)

        # Create CompositeAudioClip for the speech
        speech_clip = CompositeAudioClip([AudioFileClip('speech.mp3')])

        # Set the audio of the final video to be the speech
        final_clip = final_clip.set_audio(speech_clip)

        # Write the final video to file
        video_path = os.path.join(IMAGE_DIR, 'output_video.mp4')
        final_clip.write_videofile(video_path, codec="libx264", fps=1)

        return jsonify({'video_path': video_path, 'translated_text': translated_text})

@app.route('/images/<path:filename>')
def download_file(filename):
    return send_from_directory(IMAGE_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
