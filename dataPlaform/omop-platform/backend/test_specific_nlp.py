# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.transformers_ner import TransformersNERMapper


mapper = TransformersNERMapper()
samples = [
    "空腹血糖: 6.5, 餐后血糖: 8.0趋势平稳，关节疼痛1周。",
    "患者主诉胸闷憋气，查体发现右上腹压痛，既往有冠心病支架植入史，初步印象为急性胆囊炎。",
]

for idx, text in enumerate(samples, start=1):
    print(f"===== sample_{idx} =====")
    result = mapper.extract_entities(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
