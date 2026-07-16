from app.services.staging_transformer import StagingTransformer


def test_parse_nlp_medication_value():
    parsed = StagingTransformer._parse_nlp_medication_value("药名：阿司匹林 剂型：肠溶片 给药方式：口服")

    assert parsed == ("阿司匹林", "肠溶片", "口服")


def test_parse_medication_components_supports_free_text_prescription():
    parsed = StagingTransformer._parse_medication_components("氨氯地平片 5mg qd")

    assert parsed == {
        "name": "氨氯地平",
        "form": "片",
        "route": "口服",
        "dose": "5mg",
        "frequency": "qd",
    }


def test_parse_medication_components_supports_structured_nlp_format():
    parsed = StagingTransformer._parse_medication_components("药名：氨氯地平 剂型：片 给药方式：口服 剂量：5mg 频次：qd")

    assert parsed == {
        "name": "氨氯地平",
        "form": "片",
        "route": "口服",
        "dose": "5mg",
        "frequency": "qd",
    }


def test_parse_nlp_symptom_value_supports_duration_format():
    parsed = StagingTransformer._parse_nlp_symptom_value("症状：胸闷 持续时间：1周")

    assert parsed == ("胸闷", "1周", "持续时间")
