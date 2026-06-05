import os
import time
import logging
import asyncio
import httpx
import base64
import tempfile
import uuid

logger = logging.getLogger(__name__)

SADTALKER_URL = "http://192.168.0.214:7860"

def _call_sadtalker_sync(image_path: str, audio_path: str) -> str:
    """使用 httpx 同步调用 SadTalker"""
    logger.info("Sending predict request to SadTalker via httpx...")
    
    url = f"{SADTALKER_URL}/run/predict"
    
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    payload = {
        "data": [
            f"data:image/jpeg;base64,{img_b64}",
            {"name": "audio.wav", "data": f"data:audio/wav;base64,{audio_b64}"},
            "full",  # preprocess
            True,    # still_mode
            False,   # gfpgan_as_face_enhancer
            2,       # batch_size_in_generation
            256,     # face_model_resolution (SadTalker code expects integer 256 or 512 for img_size calculation)
            0        # pose_style
        ],
        "fn_index": 1
    }
    
    try:
        with httpx.Client(timeout=None) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            if "data" in data and len(data["data"]) > 0:
                video_data = data["data"][0]
                if isinstance(video_data, dict) and "name" in video_data:
                    # In Gradio 3, the video might be returned as a dict with 'name'
                    video_url = f"{SADTALKER_URL}/file={video_data['name']}"
                    video_resp = client.get(video_url)
                    if video_resp.status_code == 200:
                        output_path = os.path.join(tempfile.gettempdir(), f"avatar_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4")
                        with open(output_path, "wb") as vf:
                            vf.write(video_resp.content)
                        return output_path
                elif isinstance(video_data, str) and video_data.startswith("data:video"):
                    # base64 embedded
                    header, encoded = video_data.split(",", 1)
                    output_path = os.path.join(tempfile.gettempdir(), f"avatar_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4")
                    with open(output_path, "wb") as vf:
                        vf.write(base64.b64decode(encoded))
                    return output_path
                elif isinstance(video_data, list):
                    # sometimes it returns a list of files
                    if len(video_data) > 0 and isinstance(video_data[0], dict) and "name" in video_data[0]:
                        video_url = f"{SADTALKER_URL}/file={video_data[0]['name']}"
                        video_resp = client.get(video_url)
                        if video_resp.status_code == 200:
                            output_path = os.path.join(tempfile.gettempdir(), f"avatar_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4")
                            with open(output_path, "wb") as vf:
                                vf.write(video_resp.content)
                            return output_path
            
            logger.error(f"SadTalker unexpected response format: {data}")
            return ""
            
    except Exception as e:
        logger.error(f"SadTalker 调用失败: {e}")
        return ""

async def generate_avatar_video(image_path: str, audio_path: str) -> str:
    """异步包装器，防止阻塞主线程"""
    logger.info(f"Calling SadTalker via httpx wrapper... Image: {image_path}, Audio: {audio_path}")
    loop = asyncio.get_event_loop()
    video_path = await loop.run_in_executor(None, _call_sadtalker_sync, image_path, audio_path)
    if video_path and os.path.exists(video_path):
        logger.info(f"Avatar video generated successfully: {video_path}")
        return video_path
    else:
        logger.error("Avatar video generation failed.")
        return ""
