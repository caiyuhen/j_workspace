import wave
import sys
from backend.services.tts_service import generate_doctor_speech

text = "您好，我为您诊断一下。这很可能是原发性高血压引起的。"
path = generate_doctor_speech(text, "female")
print("Generated path:", path)

with wave.open(path, "rb") as w:
    print(f"Channels: {w.getnchannels()}, SampWidth: {w.getsampwidth()}, Rate: {w.getframerate()}")
