from flask import Blueprint, render_template, request, jsonify
from moviepy.editor import ImageSequenceClip, concatenate_videoclips, CompositeAudioClip, AudioFileClip, TextClip, CompositeVideoClip
from PIL import Image
import os

upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/upload_images', methods=['POST'])
def upload_images():
    # Check if the request contains files
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files found'}), 400

    files = request.files.getlist('files[]')

    # Check the number of files uploaded
    if len(files) > 5:
        return jsonify({'error': 'You can upload a maximum of 5 images'}), 400

    # Directory to save uploaded images
    UPLOAD_DIR = 'uploaded_images'

    # Create the upload directory if it doesn't exist
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # Save the uploaded images
    uploaded_image_paths = []
    for file in files:
        if file.filename == '':
            continue
        filename = file.filename
        file_path = os.path.join(UPLOAD_DIR, filename)
        file.save(file_path)
        uploaded_image_paths.append(file_path)

    # Generate video from uploaded images
    final_clip = generate_video(uploaded_image_paths)

    # Attach the previously generated speech
    speech_clip = AudioFileClip('speech.mp3')
    final_clip = final_clip.set_audio(speech_clip)

    # Generate subtitles from translated text
    translated_text = request.form.get('translated_text')
    speech_duration = speech_clip.duration
    subtitles = generate_subtitles(translated_text, speech_duration)

    # Overlay subtitles onto the video
    final_clip = overlay_subtitles(final_clip, subtitles)

    # Write the final video to file
    video_path = os.path.join(UPLOAD_DIR, 'output_video.mp4')
    final_clip.write_videofile(video_path, codec="libx264", fps=1)

    return jsonify({'video_path': video_path})

def generate_video(image_paths):
    # Calculate the duration of each image clip
    num_images = len(image_paths)
    speech_duration = AudioFileClip('speech.mp3').duration
    image_duration = speech_duration / num_images

    # Create video clips from resized images
    video_clips = []
    for img_path in image_paths:
        img = Image.open(img_path)
        img = img.resize((1280, 720))  # Resize images to 1280x720
        clip = ImageSequenceClip([img_path], durations=[image_duration])
        video_clips.append(clip)

    # Concatenate video clips to create the final video
    final_clip = concatenate_videoclips(video_clips)
    return final_clip

def generate_subtitles(text, duration):
    """Generate subtitles from text and duration."""
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

def overlay_subtitles(clip, subtitles):
    """Overlay subtitles onto the clip."""
    annotated_clips = []
    for start_time, end_time, subtitle_text in subtitles:
        txt_clip = TextClip(subtitle_text, fontsize=36, color='white', bg_color='black', font='Arial-Bold')
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(end_time - start_time).set_start(start_time)
        annotated_clips.append(txt_clip)
    return CompositeVideoClip([clip] + annotated_clips)