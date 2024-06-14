from moviepy.editor import ImageSequenceClip, concatenate_videoclips, CompositeAudioClip, AudioFileClip, TextClip, CompositeVideoClip
import spacy
import os
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from PIL import Image
from googletrans import Translator

app = Flask(__name__, static_url_path='/static')

# Define your Unsplash API access key
UNSPLASH_ACCESS_KEY = 'w8z8J5TU-1NfjieaG0lIAlpGZ09JLKogSkt3fU3_TH8'

# Directory to save downloaded images
IMAGE_DIR = 'images'

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

        # Generate speech.mp3 from translated text
        speech_url = "https://api.elevenlabs.io/v1/text-to-speech/8CSj1uBcRBgnnKjtWTWP"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": "e8a55721032782c94f7bae0a60a17b8c"
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

        # Get the duration of the speech
        speech_duration = AudioFileClip('speech.mp3').duration

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

        # Sort keywords based on their appearance in the summarized text
        sorted_keywords = []
        for keyword in processed_keywords:
            if keyword in key_points:
                sorted_keywords.append(keyword)
        sorted_keywords.sort(key=lambda x: key_points.index(x))

        # Resize images to the same dimensions based on sorted keywords
        resized_images = []
        for keyword in sorted_keywords:
            img_path = os.path.join(IMAGE_DIR, f'{keyword}_image.jpg')
            img = Image.open(img_path)
            img = img.resize((1280, 720))  # Resize images to 1280x720
            resized_img_path = os.path.join(IMAGE_DIR, f'resized_{keyword}_image.jpg')
            img.save(resized_img_path)
            resized_images.append(resized_img_path)

        # Calculate the duration of each image clip
        num_images = len(resized_images)
        image_duration = speech_duration / num_images

        # Create video clips from resized images
        video_clips = []
        for img_path in resized_images:
            clip = ImageSequenceClip([img_path], durations=[image_duration])  # Set the duration of each image clip
            video_clips.append(clip)

        # Concatenate video clips to create the final video
        final_clip = concatenate_videoclips(video_clips)

        # Create CompositeAudioClip for the speech
        speech_clip = CompositeAudioClip([AudioFileClip('speech.mp3')])

        # Set the audio of the final video to be the speech
        final_clip = final_clip.set_audio(speech_clip)

        # Generate subtitles from translated text
        subtitles = generate_subtitles(translated_text, speech_duration, selected_language)

        # Overlay subtitles onto the video
        final_clip = overlay_subtitles(final_clip, subtitles, selected_language)

        # Write the final video to file
        video_path = os.path.join(IMAGE_DIR, 'output_video.mp4')
        final_clip.write_videofile(video_path, codec="libx264", fps=1)

        return jsonify({'video_path': video_path, 'translated_text': translated_text})

def generate_subtitles(text, duration, language):
    """Generate subtitles from text and duration."""
    if language == 'hi':
        font = 'NirmalaUI-Regular'
    elif language == 'ta':
        font = 'Bamini-Regular'
    else:
        font = 'Arial-Bold'
        
    words = text.split()
    num_words = len(words)
    word_duration = duration / num_words
    lines = []
    line = ''
    for word in words:
        if len(line.split()) < 4:
            line += word + ' '
        else:
            lines.append(line.strip())
            line = word + ' '
    if line:
        lines.append(line.strip())
    num_lines = len(lines)
    line_duration = duration / num_lines
    subtitles = [(i * line_duration, (i + 1) * line_duration, lines[i]) for i in range(num_lines)]
    return subtitles

def overlay_subtitles(clip, subtitles, language):
    """Overlay subtitles onto the clip."""
    annotated_clips = []
    for start_time, end_time, subtitle_text in subtitles:
        if language == 'hi':
            txt_clip = TextClip(subtitle_text, fontsize=36, color='white', bg_color='black', font='NirmalaUI-Regular')
        elif language == 'ta':
            txt_clip = TextClip(subtitle_text, fontsize=36, color='white', bg_color='black', font='Bamini-Regular')
        else:
            txt_clip = TextClip(subtitle_text, fontsize=36, color='white', bg_color='black', font='Arial-Bold')
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(end_time - start_time).set_start(start_time)
        annotated_clips.append(txt_clip)
    return CompositeVideoClip([clip] + annotated_clips)

@app.route('/images/<path:filename>')
def download_file(filename):
    return send_from_directory(IMAGE_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
