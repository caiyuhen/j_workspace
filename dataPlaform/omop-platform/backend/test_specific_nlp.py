# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.transformers_ner import TransformersNERMapper

mapper = TransformersNERMapper()
text = "患者主诉胸闷憋气，查体发现右上腹压痛，既往有冠心病支架植入史，初步印象为急性胆囊炎。"
result = mapper.extract_entities(text)

import json
print(json.dumps(result, ensure_ascii=False, indent=2))