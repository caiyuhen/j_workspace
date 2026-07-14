from app.services.transformers_ner import TransformersNERMapper


def test_regex_extracts_specimen_and_care_site_domains():
    mapper = object.__new__(TransformersNERMapper)

    result, residual = mapper._build_regex_result("患者于心内科留取静脉血复查。")

    assert "静脉血" in result["specimens"]
    assert "心内科" in result["care_sites"]
    assert "静脉血" not in residual
    assert "心内科" not in residual


def test_parse_llm_content_supports_new_domains():
    mapper = object.__new__(TransformersNERMapper)

    content = (
        '{"conditions":[],"medications":[],"procedures":["冠脉CTA"],'
        '"observations":[],"devices":["冠脉支架"],"specimens":["静脉血"],'
        '"death":["抢救无效死亡"],"providers":["李主任"],"care_sites":["心内科"]}'
    )

    result = mapper._parse_llm_content(content)

    assert result["procedures"] == ["冠脉CTA"]
    assert result["devices"] == ["冠脉支架"]
    assert result["specimens"] == ["静脉血"]
    assert result["death"] == ["抢救无效死亡"]
    assert result["providers"] == ["李主任"]
    assert result["care_sites"] == ["心内科"]
