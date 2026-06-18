from app.services.deliverable_format import infer_deliverable_format


def test_infer_pptx_when_prompt_asks_for_ppt_even_if_default_docx():
    prompt = "帮我检查一下关于糖尿病GLP-1治疗的最新研究成果，做一个解读的PPT"

    assert infer_deliverable_format(prompt, requested_format="docx") == "pptx"


def test_infer_docx_when_prompt_explicitly_asks_word():
    assert infer_deliverable_format("生成一个Word研究方案", requested_format="pptx") == "docx"


def test_infer_xlsx_when_prompt_asks_excel_table():
    assert infer_deliverable_format("整理成Excel表格", requested_format="docx") == "xlsx"


def test_keep_requested_format_when_prompt_has_no_format_hint():
    assert infer_deliverable_format("总结最新研究成果", requested_format="docx") == "docx"
