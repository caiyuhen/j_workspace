import subprocess
import os
import shutil

text = "您好，我是您的专属数字孪生医生。我将为您提供专业的医疗建议和健康管理方案。请随时告诉我您的症状。我在这里随时准备回答您的健康问题。"

# Generate TTS using edge-tts
subprocess.run([
    "edge-tts", "--text", text, "--voice", "zh-CN-YunxiNeural", "--write-media", "temp_prompt.mp3"
])

# Convert to WAV 24000Hz mono using ffmpeg
subprocess.run([
    "ffmpeg", "-y", "-i", "temp_prompt.mp3",
    "-ar", "24000", "-ac", "1",
    "/home/user/Dr_Digital_Twin_Project/docs/male_audio_prompt.wav"
])

# For female, let's generate a female voice
female_text = "您好，我是您的专属数字孪生医生。我将为您提供专业的医疗建议和健康管理方案。请随时告诉我您的症状。"
subprocess.run([
    "edge-tts", "--text", female_text, "--voice", "zh-CN-XiaoxiaoNeural", "--write-media", "temp_prompt_f.mp3"
])

subprocess.run([
    "ffmpeg", "-y", "-i", "temp_prompt_f.mp3",
    "-ar", "24000", "-ac", "1",
    "/home/user/Dr_Digital_Twin_Project/docs/female_audio_prompt.wav"
])

os.remove("temp_prompt.mp3")
os.remove("temp_prompt_f.mp3")
print("Chinese prompts generated successfully!")
