import requests

CHUNK_SIZE = 1024
url = "https://api.elevenlabs.io/v1/text-to-speech/w3f1jPfQu2u73QtB7iTl"

headers = {
  "Accept": "audio/mpeg",
  "Content-Type": "application/json",
  "xi-api-key": "195ec3bd763f2acd7f58f2a826301f90"
}

data = {
  "text": "The value of Education",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.5
  },
  "model_id": "eleven_multilingual_v2"  # Add the model_id parameter
}

response = requests.post(url, json=data, headers=headers)
with open('output.mp3', 'wb') as f:
    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunk:
            f.write(chunk)
