import os
import tempfile
from TTS.api import TTS


class TTSTalker():
    def __init__(self) -> None:
        try:
            models = TTS().list_models()
            if isinstance(models, list):
                model_name = models[0]
            else:
                models_dict = getattr(models, 'models_dict', getattr(models, 'models', {}))
                model_name = list(models_dict.keys())[0] if models_dict else "tts_models/multilingual/multi-dataset/your_tts"
        except Exception:
            model_name = "tts_models/multilingual/multi-dataset/your_tts"
            
        if not isinstance(model_name, str) or model_name.count('/') != 3:
            model_name = "tts_models/multilingual/multi-dataset/your_tts"
            
        self.tts = TTS(model_name)

    def test(self, text, language='en'):

        tempf  = tempfile.NamedTemporaryFile(
                delete = False,
                suffix = ('.'+'wav'),
            )

        kwargs = {
            "text": text,
            "file_path": tempf.name
        }
        if self.tts.speakers and len(self.tts.speakers) > 0:
            kwargs["speaker"] = self.tts.speakers[0]
        if self.tts.languages and len(self.tts.languages) > 0:
            kwargs["language"] = language if language in self.tts.languages else self.tts.languages[0]

        self.tts.tts_to_file(**kwargs)

        return tempf.name
