from gtts import gTTS
import os
import subprocess

text = "您好，我是您的专属数字孪生医生。我将为您提供专业的医疗建议和健康管理方案。请随时告诉我您的症状。"

# Generate TTS
tts = gTTS(text=text, lang='zh-cn')
tts.save("temp_prompt.mp3")

# Convert to WAV 24000Hz mono using ffmpeg
subprocess.run([
    "ffmpeg", "-y", "-i", "temp_prompt.mp3",
    "-ar", "24000", "-ac", "1",
    "/home/user/Dr_Digital_Twin_Project/docs/male_audio_prompt.wav"
])

# Also copy for female
import shutil
shutil.copy("/home/user/Dr_Digital_Twin_Project/docs/male_audio_prompt.wav", 
            "/home/user/Dr_Digital_Twin_Project/docs/female_audio_prompt.wav")

os.remove("temp_prompt.mp3")
print("Chinese prompts generated successfully!")
