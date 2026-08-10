from pydantic import BaseModel


class SourceCatalogItem(BaseModel):
    key: str
    label: str
    description: str
    supports_full_text: bool


class CatalogOption(BaseModel):
    key: str
    label: str


SOURCE_CATALOG: list[SourceCatalogItem] = [
    SourceCatalogItem(
        key="pubmed",
        label="PubMed",
        description="美国国立医学图书馆生物医学文献库",
        supports_full_text=False,
    ),
    SourceCatalogItem(
        key="embase",
        label="Embase",
        description="爱思唯尔生物医学与药理学文献库",
        supports_full_text=False,
    ),
    SourceCatalogItem(
        key="cochrane",
        label="Cochrane Library",
        description="系统评价与随机对照试验证据库",
        supports_full_text=True,
    ),
    SourceCatalogItem(
        key="wos",
        label="Web of Science",
        description="跨学科引文索引数据库",
        supports_full_text=False,
    ),
    SourceCatalogItem(
        key="cnki",
        label="中国知网 CNKI",
        description="中文学术期刊与学位论文库",
        supports_full_text=True,
    ),
    SourceCatalogItem(
        key="wanfang",
        label="万方数据",
        description="中文医药卫生与科技文献库",
        supports_full_text=True,
    ),
]

SEARCH_FIELD_OPTIONS: list[CatalogOption] = [
    CatalogOption(key="title", label="标题"),
    CatalogOption(key="abstract", label="摘要"),
    CatalogOption(key="keyword", label="关键词"),
    CatalogOption(key="mesh", label="主题词"),
    CatalogOption(key="full_text", label="全文"),
]

LANGUAGE_OPTIONS: list[CatalogOption] = [
    CatalogOption(key="en", label="英文"),
    CatalogOption(key="zh", label="中文"),
]

SOURCE_KEYS = {item.key for item in SOURCE_CATALOG}
SEARCH_FIELD_KEYS = {item.key for item in SEARCH_FIELD_OPTIONS}
LANGUAGE_KEYS = {item.key for item in LANGUAGE_OPTIONS}


def source_labels_for_keys(keys: list[str]) -> list[str]:
    """按目录顺序把来源 key 转成展示 label，未知 key 直接忽略。"""
    selected = set(keys)
    return [item.label for item in SOURCE_CATALOG if item.key in selected]
