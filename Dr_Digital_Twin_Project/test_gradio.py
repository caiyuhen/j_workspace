import os
from gradio_client import Client, handle_file

client = Client("http://192.168.0.214:7778")

text = "老王，您当前空腹血糖八点五摩尔每升（高于正常范围小于六点一摩尔每升），收缩压一百四十五毫米汞柱（提示高血压，正常小于一百二十毫米汞柱），系统风险评估为高危，结合“头痛”主诉，需高度警惕糖尿病相关并发症（如糖尿病性脑血管病变、高血糖性头痛）及高血压性头痛。"

try:
    print("Testing with problematic text chunk...")
    result = client.predict(
        text=text,
        audio_prompt_path=handle_file("/home/user/Dr_Digital_Twin_Project/docs/male_audio_prompt.wav"),
        temperature=0.8,
        seed_num=0,
        min_p=0.05,
        top_p=1.0,
        top_k=1000,
        repetition_penalty=2.0,
        norm_loudness=True,
        api_name="/generate_speech"
    )
    print("Success:", result)
except Exception as e:
    print("Error:", e)
