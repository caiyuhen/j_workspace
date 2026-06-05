import cn2an
from backend.services.tts_service import convert_to_medical_tts_text

text = '老王，您当前空腹血糖8.5mmol/L（高于正常空腹血糖<6.1mmol/L），收缩压145mmHg（高于正常<120mmHg），提示存在明确的糖尿病前期及高血压，结合“头痛、头晕”主诉，需高度警惕高血压脑病或糖尿病相关脑血管自主神经功能紊乱。建议立即启动降压治疗，目标收缩压<130mmHg，推荐使用ACEI类药物（如贝那普利10mg qd）'
print(convert_to_medical_tts_text(text))

text2 = 'GLP-1受体激动剂（如利拉鲁肽）'
print(convert_to_medical_tts_text(text2))

