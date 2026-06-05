import httpx
import sys

# We'll mock httpx.post
original_post = httpx.Client.post

def mock_post(self, url, *args, **kwargs):
    if "call/generate_speech" in url:
        print("POST URL:", url)
        print("POST JSON:", kwargs.get("json"))
    return original_post(self, url, *args, **kwargs)

httpx.Client.post = mock_post

from gradio_client import Client, handle_file
import os

client = Client("http://192.168.0.214:7778/")
prompt_path = os.path.join(os.getcwd(), "docs", "male_audio_prompt.wav")
result = client.predict(
    text="您好，我是测试",
    audio_prompt_path=handle_file(prompt_path),
    temperature=1.5,
    seed_num=0,
    min_p=0.0,
    top_p=0.95,
    top_k=1000,
    repetition_penalty=1.2,
    norm_loudness=True,
    api_name="/generate_speech",
)
print("RESULT:", result)
