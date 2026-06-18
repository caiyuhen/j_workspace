from app.services.task_background_service import _extract_skill_output_text


def test_extract_skill_output_text_reads_local_skillhub_dict_output():
    response = {
        "skill_id": "skill_clinical_data_cleaner",
        "result": {
            "skill": "clinical_data_cleaner",
            "output": "## 数据管理计划\n\n- 数据核查\n- 质控流程",
            "execution_mode": "local_skillhub_pack",
        },
    }

    assert _extract_skill_output_text(response) == "## 数据管理计划\n\n- 数据核查\n- 质控流程"


def test_extract_skill_output_text_skips_converter_execution_reports():
    response = {
        "skill_id": "skill_md2docx",
        "result": {
            "skill": "md2docx",
            "output": "# md2docx Skill 执行报告\n\n输入不足提示",
        },
    }

    assert _extract_skill_output_text(response) == ""
