import cn2an

def convert_to_medical_tts_text(text: str) -> str:
    replacements = {
        "mmol/L": "摩尔每升",
        "mmHg": "毫米汞柱",
        "cm": "厘米",
        "kg": "千克",
        "ml": "毫升",
        "<": "小于",
        ">": "大于",
        "=": "等于"
    }
    
    res = text
    for k, v in replacements.items():
        res = res.replace(k, v)
        
    try:
        res = cn2an.transform(res, "an2cn")
    except Exception as e:
        pass
        
    return res

text = "您当前空腹血糖8.5 mmol/L（高于正常<6.1 mmol/L），收缩压145 mmHg（高于理想<120 mmHg），系统风险评估为高"
print(convert_to_medical_tts_text(text))
