# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.transformers_ner import TransformersNERMapper

mapper = TransformersNERMapper()
text = "3天前 症状：发热，value：38.5 单位：度"
result = mapper.extract_entities(text)

import json
print(json.dumps(result, ensure_ascii=False, indent=2))