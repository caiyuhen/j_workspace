from app.services.skill_resolver import SkillResolver


class FakeSkillRegistry:
    def __init__(self, installed=None):
        self.installed = installed or {}
        self.discovery_calls = []

    def get_skill(self, skill_id):
        return self.installed.get(skill_id)

    def discover_skill_candidates(self, query=None, required_skill_id=None, category=None):
        self.discovery_calls.append({"query": query, "required_skill_id": required_skill_id, "category": category})
        return {
            "installed": False,
            "required_skill_id": required_skill_id,
            "query": query,
            "candidates": [
                {
                    "id": "candidate_pubmed_search",
                    "target_skill_id": "skill_pubmed_search",
                    "name": "pubmed_search",
                    "display_name": "PubMed 文献检索",
                    "description": "检索 PubMed 文献",
                    "category": "research",
                    "protocol": "skillhub",
                    "install_requires_confirmation": True,
                }
            ],
            "message": "发现候选技能",
        }


def test_skill_resolver_detects_missing_pubmed_skill_and_returns_candidates():
    resolver = SkillResolver(skill_registry=FakeSkillRegistry())

    result = resolver.resolve("请检索 PubMed 文献并生成综述")

    assert result["ready"] is False
    assert result["missing_skills"][0]["required_skill_id"] == "skill_pubmed_search"
    assert result["missing_skills"][0]["candidates"][0]["id"] == "candidate_pubmed_search"


def test_skill_resolver_allows_execution_when_required_skill_is_installed():
    registry = FakeSkillRegistry(installed={
        "skill_pubmed_search": {"id": "skill_pubmed_search", "is_active": True, "display_name": "PubMed 文献检索"}
    })
    resolver = SkillResolver(skill_registry=registry)

    result = resolver.resolve("请检索 PubMed 文献并生成综述")

    assert result["ready"] is True
    assert result["installed_skills"][0]["id"] == "skill_pubmed_search"
    assert result["missing_skills"] == []
