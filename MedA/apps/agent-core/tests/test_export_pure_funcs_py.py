from app.services.serialize_ris import _sanitize_filename_py, _truncate_field_py

def test_py_sanitize_reserved():
    assert _sanitize_filename_py('a\\b:c*d?e"f<g>h|i.txt') == "a_b_c_d_e_f_g_h_i.txt"

def test_py_sanitize_ctrl_empty_fallback():
    assert _sanitize_filename_py("   \x00\x01   ", fallback="fallback.bin") == "fallback.bin"

def test_py_truncate_cjk_bytes():
    cjk = "一二三四五六七八九十"
    res = _truncate_field_py(cjk, 20)
    assert "[truncated]" in res
    assert len(res.encode("utf-8")) <= 20 + 20

def test_py_truncate_null_empty():
    assert _truncate_field_py(None, 100) == ""
