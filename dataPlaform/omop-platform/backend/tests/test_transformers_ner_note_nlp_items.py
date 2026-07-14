from app.services.transformers_ner import TransformersNERMapper


def test_regex_builds_structured_note_nlp_items():
    mapper = object.__new__(TransformersNERMapper)
    text = "否认糖尿病，空腹血糖: 6.5，胸闷1周，静脉血送检。"

    result, _ = mapper._build_regex_result(text)

    items = result["note_nlp_items"]

    assert any(item["domain"] == "negation" and item["text"] == "诊断：糖尿病 ，否定词：否认" for item in items)
    assert any(item["domain"] == "measurement" and item["normalized_value"] == "空腹血糖" for item in items)
    assert any(item["domain"] == "symptom" and item["normalized_value"] == "症状：胸闷" for item in items)
    assert any(item["domain"] == "specimen" and item["text"] == "静脉血" for item in items)
    assert any(item["domain"] == "negation" and item["source_layer"] == "regex" and item["negated"] is True for item in items)
    assert any(item["domain"] == "measurement" and item["source_layer"] == "regex" and item["negated"] is False for item in items)

    measurement_item = next(item for item in items if item["domain"] == "measurement")
    assert measurement_item["offset_start"] == text.index("空腹血糖")
    assert measurement_item["offset_end"] == text.index("6.5") + len("6.5")

    specimen_item = next(item for item in items if item["domain"] == "specimen")
    assert specimen_item["offset_start"] == text.index("静脉血")
    assert specimen_item["offset_end"] == text.index("静脉血") + len("静脉血")


def test_ner_collects_note_nlp_items_with_confidence():
    mapper = object.__new__(TransformersNERMapper)
    mapper.LLM_NER_CONFIDENCE_THRESHOLD = 0.78
    text = "患者冠心病并行支架植入术。"

    result, _, _ = mapper._collect_ner_result(
        text,
        [
            {"entity_group": "DIS", "word": "冠心病", "score": 0.95},
            {"entity_group": "PROCEDURE", "word": "支架植入术", "score": 0.96},
        ],
    )

    items = result["note_nlp_items"]

    assert any(item["domain"] == "condition" and item["text"] == "冠心病" and item["confidence"] == 0.95 for item in items)
    assert any(item["domain"] == "procedure" and item["text"] == "支架植入术" and item["confidence"] == 0.96 for item in items)
    assert all(item["source_layer"] == "ner" for item in items)
    assert all(item["negated"] is False for item in items)

    condition_item = next(item for item in items if item["domain"] == "condition")
    assert condition_item["offset_start"] == text.index("冠心病")
    assert condition_item["offset_end"] == text.index("冠心病") + len("冠心病")

    procedure_item = next(item for item in items if item["domain"] == "procedure")
    assert procedure_item["offset_start"] == text.index("支架植入术")
    assert procedure_item["offset_end"] == text.index("支架植入术") + len("支架植入术")


def test_ner_repeated_entities_use_stable_non_overlapping_offsets():
    mapper = object.__new__(TransformersNERMapper)
    mapper.LLM_NER_CONFIDENCE_THRESHOLD = 0.78
    text = "冠心病复诊，既往冠心病病史。"

    result, _, _ = mapper._collect_ner_result(
        text,
        [
            {"entity_group": "DIS", "word": "冠心病", "score": 0.95},
            {"entity_group": "DIS", "word": "冠心病", "score": 0.93},
        ],
    )

    items = [item for item in result["note_nlp_items"] if item["domain"] == "condition"]

    assert len(items) == 2
    assert items[0]["offset_start"] == text.index("冠心病")
    assert items[0]["offset_end"] == text.index("冠心病") + len("冠心病")

    second_start = text.index("冠心病", items[0]["offset_end"])
    assert items[1]["offset_start"] == second_start
    assert items[1]["offset_end"] == second_start + len("冠心病")


def test_llm_parse_synthesizes_note_nlp_items():
    mapper = object.__new__(TransformersNERMapper)
    text = "患者急性胆囊炎，完善冠脉CTA，置入冠脉支架，李主任于心内科查体见右上腹压痛。"

    result = mapper._parse_llm_content(
        '{"conditions":["急性胆囊炎"],"medications":[],"procedures":["冠脉CTA"],'
        '"observations":["右上腹压痛"],"devices":["冠脉支架"],"specimens":[],"death":[],"providers":["李主任"],"care_sites":["心内科"]}',
        original_text=text,
    )

    items = result["note_nlp_items"]

    assert any(item["domain"] == "condition" and item["text"] == "急性胆囊炎" for item in items)
    assert any(item["domain"] == "procedure" and item["text"] == "冠脉CTA" for item in items)
    assert any(item["domain"] == "device" and item["text"] == "冠脉支架" for item in items)
    assert any(item["domain"] == "provider" and item["text"] == "李主任" for item in items)
    assert any(item["domain"] == "care_site" and item["text"] == "心内科" for item in items)
    assert all(item["source_layer"] == "llm" for item in items)
    assert all(item["negated"] is False for item in items)

    provider_item = next(item for item in items if item["domain"] == "provider")
    assert provider_item["offset_start"] == text.index("李主任")
    assert provider_item["offset_end"] == text.index("李主任") + len("李主任")

    care_site_item = next(item for item in items if item["domain"] == "care_site")
    assert care_site_item["offset_start"] == text.index("心内科")
    assert care_site_item["offset_end"] == text.index("心内科") + len("心内科")


def test_llm_parse_prefers_text_and_falls_back_to_normalized_value_for_offsets():
    mapper = object.__new__(TransformersNERMapper)
    text = "患者完善冠脉CTA，术后冠状动脉CT血管成像结果已回报。"

    result = mapper._parse_llm_content(
        '{"conditions":[],"medications":[],"procedures":['
        '{"text":"冠脉CTA","normalized_value":"冠状动脉CT血管成像"},'
        '{"text":"CTA随访","normalized_value":"冠状动脉CT血管成像"}'
        '],"observations":[],"devices":[],"specimens":[],"death":[],"providers":[],"care_sites":[]}',
        original_text=text,
    )

    items = [item for item in result["note_nlp_items"] if item["domain"] == "procedure"]

    assert len(items) == 2
    assert items[0]["text"] == "冠脉CTA"
    assert items[0]["normalized_value"] == "冠状动脉CT血管成像"
    assert items[0]["offset_start"] == text.index("冠脉CTA")
    assert items[0]["offset_end"] == text.index("冠脉CTA") + len("冠脉CTA")

    normalized_start = text.index("冠状动脉CT血管成像")
    assert items[1]["text"] == "CTA随访"
    assert items[1]["normalized_value"] == "冠状动脉CT血管成像"
    assert items[1]["offset_start"] == normalized_start
    assert items[1]["offset_end"] == normalized_start + len("冠状动脉CT血管成像")


def test_regex_assigns_inline_note_sections_by_offset():
    mapper = object.__new__(TransformersNERMapper)
    text = "现病史：胸闷1周。辅助检查：空腹血糖: 6.5。"

    result, _ = mapper._build_regex_result(text)

    symptom_item = next(item for item in result["note_nlp_items"] if item["domain"] == "symptom")
    measurement_item = next(item for item in result["note_nlp_items"] if item["domain"] == "measurement")

    assert symptom_item["section"] == "现病史"
    assert measurement_item["section"] == "辅助检查"


def test_llm_assigns_inline_note_sections_by_offset():
    mapper = object.__new__(TransformersNERMapper)
    text = "现病史：胸闷憋气。查体：右上腹压痛。辅助检查：冠脉CTA。"

    result = mapper._parse_llm_content(
        '{"conditions":[],"medications":[],"procedures":["冠脉CTA"],'
        '"observations":["右上腹压痛"],"devices":[],"specimens":[],"death":[],"providers":[],"care_sites":[]}',
        original_text=text,
    )

    observation_item = next(item for item in result["note_nlp_items"] if item["domain"] == "observation")
    procedure_item = next(item for item in result["note_nlp_items"] if item["domain"] == "procedure")

    assert observation_item["section"] == "查体"
    assert procedure_item["section"] == "辅助检查"
