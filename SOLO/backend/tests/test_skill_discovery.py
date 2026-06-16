from app.services.skill_registry import SkillRegistry


def test_discover_missing_skill_returns_candidates_without_installing():
    registry = SkillRegistry()
    before_ids = {skill["id"] for skill in registry.list_skills()}

    result = registry.discover_skill_candidates(query="文献检索 pubmed", required_skill_id="skill_pubmed_search")

    after_ids = {skill["id"] for skill in registry.list_skills()}
    assert before_ids == after_ids
    assert result["installed"] is False
    assert result["required_skill_id"] == "skill_pubmed_search"
    assert result["candidates"]
    assert any(candidate["id"] == "candidate_pubmed_search" for candidate in result["candidates"])


def test_install_candidate_requires_explicit_call():
    registry = SkillRegistry()

    assert registry.get_skill("skill_pubmed_search") is None
    skill = registry.install_candidate("candidate_pubmed_search")

    assert skill["id"] == "skill_pubmed_search"
    assert skill["name"] == "pubmed_search"
    assert registry.get_skill("skill_pubmed_search") is not None


def test_install_candidate_rejects_unknown_candidate():
    registry = SkillRegistry()

    try:
        registry.install_candidate("candidate_not_exist")
    except ValueError as exc:
        assert "候选技能不存在" in str(exc)
    else:
        raise AssertionError("未知候选技能应该被拒绝")
