from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import requests
from moviepy.editor import ImageSequenceClip, concatenate_videoclips, CompositeAudioClip, AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = 'static'


def generate_subtitles(text, duration):
    """Generate subtitles from text and duration."""
    num_words = len(text.split())
    word_duration = duration / num_words
    lines = [text[i:i + 4 * 15] for i in range(0, len(text), 4 * 15)]
    num_lines = len(lines)
    line_duration = duration / num_lines
    subtitles = [(i * line_duration, (i + 1) * line_duration, lines[i]) for i in range(num_lines)]
    return subtitles


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_video', methods=['POST'])
def generate_video():
    text = request.form['text']
    files = request.files.getlist('file[]')

    # Generate speech.mp3 from text
    speech_url = "https://api.elevenlabs.io/v1/text-to-speech/w3f1jPfQu2u73QtB7iTl"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": "7f1231d6cffac95aa5b634ba2de78442"
    }
    speech_data = {
        "text": text,
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

    # Process uploaded images
    image_paths = []
    for file in files:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image_paths.append(file_path)

    # Calculate the duration of each image clip
    num_images = len(image_paths)
    image_duration = speech_duration / num_images

    # Create video clips from uploaded images
    video_clips = []
    for img_path in image_paths:
        clip = ImageSequenceClip([img_path], durations=[image_duration])
        video_clips.append(clip)

    # Concatenate video clips to create the final video
    final_clip = concatenate_videoclips(video_clips)

    # Create CompositeAudioClip for the speech
    speech_clip = CompositeAudioClip([AudioFileClip('speech.mp3')])

    # Set the audio of the final video to be the speech
    final_clip = final_clip.set_audio(speech_clip)

    # Generate subtitles
    subtitles = generate_subtitles(text, speech_duration)

    # Overlay subtitles onto the video
    for start_time, end_time, subtitle_text in subtitles:
        txt_clip = final_clip.subclip(start_time, end_time).\
            set_position(('center', 'bottom')).\
            set_duration(end_time - start_time)
        final_clip = CompositeVideoClip([final_clip, txt_clip])

    # Write the final video to file in the static folder
    video_path = os.path.join(app.config['STATIC_FOLDER'], 'output_video.mp4')
    final_clip.write_videofile(video_path, codec="libx264", fps=1)

    return jsonify({'video_path': video_path, 'speech_duration': speech_duration})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    # Run the Flask app on port 8080
    app.run(debug=True, port=8080)
