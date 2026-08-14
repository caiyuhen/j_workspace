"""Offline parse tests for CNKI/Wanfang with fixed HTML stub cards."""
from app.services.sources.cnki_adapter import _parse_cnki_list_html
from app.services.sources.wanfang_adapter import _parse_wanfang_list_html

CNKI_STUB_HTML = """
<html><body>
<div class="result-table">
  <table>
    <tr>
      <td class="name"><a class="fz14" href="https://kns.cnki.net/kcms2/article/abstract?filename=CJFQ20240001&dbname=CJFD2024">二甲双胍联合 SGLT2 抑制剂治疗 2 型糖尿病合并慢性肾病疗效观察</a></td>
      <td class="author">李明;王建国;赵丽</td>
      <td class="source">《中华内分泌代谢杂志》 2024年 第1期 33-41</td>
      <td class="abstract">目的 观察二甲双胍联合 SGLT2i 治疗 T2DM 合并 CKD 的疗效，评估 eGFR 改善情况。方法 120 例患者分组对照。</td>
    </tr>
    <tr>
      <td class="name"><a class="fz14" href="https://kns.cnki.net/kcms2/article/abstract?filename=CJFQ20232345&dbname=CJFDLAST2023">GLP-1 RA 对心血管结局影响的真实世界研究（单中心）</a></td>
      <td class="author">张伟;刘芳</td>
      <td class="source">《中国糖尿病杂志》 2023年 第11卷 888-893</td>
      <td class="abstract">回顾性纳入 210 例 T2DM 患者，观察 GLP-1 RA 与 SU 的 MACE 发生率差异。</td>
    </tr>
  </table>
</div>
</body></html>
"""

WANFANG_STUB_HTML = """
<html><body>
<div class="result-list">
  <div class="paper-item">
    <h3 class="title"><a href="/periodical/zhszb202402011">达格列净在 CKD 非糖尿病人群中的安全性 Meta 分析</a></h3>
    <div class="authors">孙志远;陈曦</div>
    <div class="source-year">《中华肾脏病杂志》 2024, Vol.40(2): 112-120</div>
    <div class="abstract">系统评价达格列净用于非 DM CKD 的安全性，纳入 8 项 RCT，结果总体安全性良好。</div>
  </div>
</div>
</body></html>
"""


def test_parse_cnki_stub_2_records_match_conftest_cnki():
    records = _parse_cnki_list_html(CNKI_STUB_HTML)
    assert len(records) == 2
    r0 = records[0]
    assert r0.source_key == "cnki"
    assert r0.title.startswith("二甲双胍联合")
    assert r0.journal == "中华内分泌代谢杂志"
    assert r0.year == 2024
    assert r0.doi == ""
    assert "SGLT2i 治疗 T2DM" in r0.abstract
    assert "CJFQ20240001" in (r0.source_record_id or "")

    r1 = records[1]
    assert r1.authors == "张伟;刘芳"
    assert r1.year == 2023
    assert "GLP-1 RA" in r1.title


def test_parse_wanfang_stub_1_record():
    records = _parse_wanfang_list_html(WANFANG_STUB_HTML)
    assert len(records) == 1
    r0 = records[0]
    assert r0.source_key == "wanfang"
    assert "达格列净" in r0.title
    assert r0.journal == "中华肾脏病杂志"
    assert r0.year == 2024
    assert "zhszb202402011" in (r0.source_record_id or "")
    assert "安全性" in r0.abstract
