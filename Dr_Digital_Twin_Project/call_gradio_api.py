import requests

url = "http://192.168.0.214:7860/api/predict"
payload = {
    "data": [
        {"path": "/app/docs/3f38645a-9a34-4539-835e-a0138327f26d.jpg"},
        {"path": "/app/docs/male_audio_prompt.wav"},
        "crop",
        True,
        True,
        2,
        256,
        0
    ],
    "fn_index": 1
}
response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())
