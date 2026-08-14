"""Offline parse test: fixed XML -> list[UnifiedLiteratureEntry] matches conftest 3 PubMed mock."""
from app.services.sources.pubmed_adapter import _parse_pubmed_xml
from tests.conftest import MOCK_PUBMED_DATASET

# 手工 XML fixture：3 条 PubmedArticle，PMID=mock_pubmed 对应的 pmid 37123457/37000001/37333333
FIXED_PUBMED_XML = """<?xml version="1.0"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMed 2024.1//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_240101.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID Version="1">37123457</PMID>
      <Article PubModel="Print-Electronic">
        <Journal>
          <Title>New England Journal of Medicine</Title>
          <JournalIssue CitedMedium="Internet">
            <Volume>388</Volume>
            <Issue>13</Issue>
            <PubDate>
              <Year>2023</Year>
              <Month>03</Month>
              <Day>30</Day>
            </PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>Dapagliflozin in Patients with <i>Chronic Kidney Disease</i></ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND" NlmCategory="BACKGROUND">The SGLT2 inhibitor in chronic kidney disease (CKD).</AbstractText>
          <AbstractText Label="METHODS" NlmCategory="METHODS">We conducted a double-blind RCT.</AbstractText>
        </Abstract>
        <AuthorList CompleteYN="Y">
          <Author><LastName>Neuen</LastName><ForeName>BL</ForeName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="pubmed">37123457</ArticleId>
        <ArticleId IdType="doi">10.1056/NEJMoa2212939</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation Status="Publisher" Owner="NLM">
      <PMID Version="1">37000001</PMID>
      <Article PubModel="Electronic">
        <Journal>
          <Title>Lancet Diabetes Endocrinol</Title>
          <JournalIssue CitedMedium="Internet">
            <PubDate>
              <Year>2023</Year>
            </PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>Effect of Empagliflozin on Cardiovascular Outcomes in T2DM with Established CVD</ArticleTitle>
        <AuthorList><Author><LastName>Zinman</LastName><ForeName>B</ForeName></Author></AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData><ArticleIdList>
      <ArticleId IdType="pubmed">37000001</ArticleId>
      <ArticleId IdType="doi">10.1016/S2213-8587(23)00042-5</ArticleId>
    </ArticleIdList></PubmedData>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID>37333333</PMID>
      <Article>
        <Journal><Title>JAMA</Title><JournalIssue><PubDate><MedlineDate>2024 May-Jun</MedlineDate></PubDate></JournalIssue></Journal>
        <ArticleTitle>Metformin plus Lifestyle versus Lifestyle Alone in Prediabetes</ArticleTitle>
        <Abstract><AbstractText>This is a RCT of Metformin plus lifestyle against lifestyle.</AbstractText></Abstract>
        <AuthorList>
          <Author><LastName>Chen</LastName><ForeName>L</ForeName></Author>
          <Author><LastName>Zhang</LastName><ForeName>Y</ForeName></Author>
          <Author><LastName>Wang</LastName><ForeName>H</ForeName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData><ArticleIdList>
      <ArticleId IdType="pubmed">37333333</ArticleId>
      <ArticleId IdType="doi">10.1001/JAMA.2023.12345</ArticleId>
    </ArticleIdList></PubmedData>
  </PubmedArticle>
</PubmedArticleSet>"""


def test_parse_pubmed_xml_matches_conftest_mock_3():
    entries = _parse_pubmed_xml(FIXED_PUBMED_XML)
    assert len(entries) == 3
    got_pmids = {e.pmid for e in entries}
    want_pmids = {m.pmid for m in MOCK_PUBMED_DATASET}
    assert got_pmids == want_pmids

    # #1 Dapagliflozin
    e1 = next(e for e in entries if e.pmid == "37123457")
    assert e1.source_key == "pubmed"
    assert e1.source_record_id == "37123457"
    assert e1.doi == MOCK_PUBMED_DATASET[0].doi  # "10.1056/nejmoa2212939"（要求小写）
    assert "Chronic Kidney Disease" in e1.title  # 标签去除
    assert "double-blind RCT" in e1.abstract  # METHODS 文本
    assert e1.journal == "New England Journal of Medicine"
    assert e1.year == 2023
    assert "Neuen BL" in e1.authors

    # #3 MedlineDate → 2024
    e3 = next(e for e in entries if e.pmid == "37333333")
    assert e3.year == 2024
    assert e3.authors.count(";") == 2  # 3 位作者 → 2 个分号分隔


def test_parse_pubmed_xml_broken_xml_returns_empty_with_catch():
    """坏 XML 情况下 prefer_real 不抛：解析失败返回空列表，异常被 _parse_pubmed_xml 吞并返回空。
    （注：force_real 情况下上层再决定是否 raise）"""
    broken = "<PubmedArticleSet><PubmedArticle></Malformed"
    result = _parse_pubmed_xml(broken)
    assert result == []


def test_parse_pubmed_xml_missing_optional_fields_sets_defaults():
    """缺 Journal/Author/Abstract/Year 不崩 → Journal="" Authors="" Abstract=None year=None"""
    xml_no_optional = """<?xml version="1.0"?>
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>99999999</PMID>
          <Article>
            <ArticleTitle>Title with <i>italic</i> nested tag</ArticleTitle>
          </Article>
        </MedlineCitation>
        <PubmedData><ArticleIdList/></PubmedData>
      </PubmedArticle>
    </PubmedArticleSet>"""
    entries = _parse_pubmed_xml(xml_no_optional)
    assert len(entries) == 1
    r = entries[0]
    assert r.pmid == "99999999"
    assert "italic nested tag" in r.title
    assert r.doi == ""
    assert r.authors == ""
    assert r.journal == ""
    assert r.year is None
    assert r.abstract == ""
