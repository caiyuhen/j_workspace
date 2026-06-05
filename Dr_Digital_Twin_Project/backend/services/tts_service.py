import os
import logging
import tempfile
import shutil
import time
import re
import cn2an
from gradio_client import Client, handle_file
import wave

logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MALE_AUDIO_PROMPT = os.path.join(base_dir, "docs", "male_audio_prompt.wav")
FEMALE_AUDIO_PROMPT = os.path.join(base_dir, "docs", "female_audio_prompt.wav")

CHATTERBOX_TTS_URL = "http://192.168.0.214:7778/"

def convert_to_medical_tts_text(text: str) -> str:
    """将大模型的返回文本转换为更适合 TTS 朗读的医疗文本"""
    if not text:
        return text
        
    replacements = {
        "mmol/L": "摩尔每升",
        "mmHg": "毫米汞柱",
        "cm": "厘米",
        "kg": "千克",
        "ml": "毫升",
        "mg": "毫克",
        " qd": " 每天一次",
        " bid": " 每天两次",
        " tid": " 每天三次",
        " qd)": " 每天一次)",
        " qd）": " 每天一次）",
        "GLP-1": "GLP一",
        "<": "小于",
        ">": "大于",
        "=": "等于"
    }
    
    res = text
    for k, v in replacements.items():
        res = res.replace(k, v)
        
    try:
        res = cn2an.transform(res, "an2cn")
        # 去除多余的空格，让TTS朗读更连贯
        # cn2an might insert spaces or translate "10mg" to "十mg" which is fine,
        # but let's fix common unit spacing
        res = res.replace(" 摩尔每升", "摩尔每升").replace(" 毫米汞柱", "毫米汞柱")
        res = res.replace(" 厘米", "厘米").replace(" 千克", "千克").replace(" 毫升", "毫升")
    except Exception as e:
        logger.warning(f"数字转中文失败: {e}")
        
    return res

class TTSService:
    def __init__(self):
        self.client = Client(CHATTERBOX_TTS_URL)
        logger.info("TTS Service initialized with Gradio Client at %s", CHATTERBOX_TTS_URL)

    def generate_speech(self, text: str, gender: str = "male") -> str:
        if not text:
            return ""
            
        # 1. 预处理文本：转换为医疗友好文本 (数字转中文等)
        text = convert_to_medical_tts_text(text)

        prompt_path = FEMALE_AUDIO_PROMPT if gender == "female" else MALE_AUDIO_PROMPT
        
        if not os.path.exists(prompt_path):
            os.makedirs(os.path.dirname(prompt_path), exist_ok=True)
            logger.warning(f"Audio prompt file not found at {prompt_path}, trying to create an empty one (this might cause TTS errors!)")
            # Create a valid minimal WAV file instead of an empty file
            with wave.open(prompt_path, 'wb') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(24000)
                f.writeframes(b'')

        output_path = os.path.join(tempfile.gettempdir(), f"output_{int(time.time())}.wav")

        try:
            import uuid
            from gradio_client import handle_file
            
            sentences = [s.strip() for s in re.split(r'([。！？.!?])', text) if s.strip()]
            chunks = []
            current_chunk = ""
            for i in range(0, len(sentences), 2):
                part = sentences[i]
                if i + 1 < len(sentences):
                    part += sentences[i+1]
                
                if len(current_chunk) + len(part) < 50:
                    current_chunk += part
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part
            if current_chunk:
                chunks.append(current_chunk)
            
            chunk_audio_paths = []
            for idx, chunk in enumerate(chunks):
                if not chunk: continue
                logger.info(f"Synthesizing chunk {idx+1}/{len(chunks)}: {chunk}")
                
                try:
                    result = self.client.predict(
                        text=chunk,
                        audio_prompt_path=handle_file(prompt_path),
                        temperature=0.8,
                        seed_num=0,
                        min_p=0.05,
                        top_p=1.0,
                        top_k=1000,
                        repetition_penalty=2.0,
                        norm_loudness=True,
                        api_name="/generate_speech"
                    )
                    
                    if isinstance(result, tuple):
                        result_path = result[0]
                    else:
                        result_path = result
                        
                    if result_path and os.path.exists(result_path):
                        chunk_path = os.path.join(tempfile.gettempdir(), f"chunk_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}.wav")
                        shutil.copy(result_path, chunk_path)
                        chunk_audio_paths.append(chunk_path)
                except Exception as ce:
                    logger.error(f"Failed to synthesize chunk: {ce}")
            
            if not chunk_audio_paths:
                raise Exception("No chunks were synthesized successfully.")
            
            data_frames = []
            params = None
            for p in chunk_audio_paths:
                with wave.open(p, 'rb') as w:
                    if not params:
                        params = w.getparams()
                    data_frames.append(w.readframes(w.getnframes()))
                try:
                    os.remove(p)
                except:
                    pass
            
            with wave.open(output_path, 'wb') as w:
                w.setparams(params)
                for frames in data_frames:
                    w.writeframes(frames)
            
            # _resample_wav_to_16k removed because audioop degrades quality
            # SadTalker handles 24000Hz internally via librosa
            logger.info(f"TTS generated and concatenated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"TTS API 调用出错: {e}")

        with open(output_path, 'wb') as f:
            f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
            
        return output_path

tts_service = TTSService()

def generate_doctor_speech(text: str, gender: str = "male") -> str:
    return tts_service.generate_speech(text, gender)
