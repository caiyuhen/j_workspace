from pathlib import Path

from app.services.artifact_service import ArtifactService


def test_create_markdown_artifact_writes_file_and_returns_download_url(tmp_path):
    service = ArtifactService(base_dir=tmp_path)

    artifact = service.create_markdown_artifact(
        user_id="user-1",
        conversation_id="conv-1",
        task_id="task-1",
        title="糖尿病研究方案",
        content="# 糖尿病研究方案\n\n正文内容",
    )

    artifact_path = Path(artifact["path"])
    assert artifact_path.exists()
    assert artifact_path.read_text(encoding="utf-8") == "# 糖尿病研究方案\n\n正文内容"
    assert artifact["filename"].endswith(".md")
    assert artifact["download_url"] == f"/api/v1/artifacts/{artifact['artifact_id']}/download"
    assert artifact["artifact_id"] in artifact["download_url"]
    assert service.get_owned_artifact(artifact["artifact_id"], "user-1")["task_id"] == "task-1"


def test_create_office_artifacts_for_docx_xlsx_pptx(tmp_path):
    service = ArtifactService(base_dir=tmp_path)

    for fmt in ["docx", "xlsx", "pptx"]:
        artifact = service.create_artifact(
            user_id="user-1",
            conversation_id="conv-1",
            task_id=f"task-{fmt}",
            title=f"测试{fmt}交付物",
            content="# 标题\n\n## 小节\n\n- 要点一\n- 要点二\n\n| 字段 | 内容 |\n|:---|:---|\n| A | B |",
            artifact_format=fmt,
        )
        artifact_path = Path(artifact["path"])
        assert artifact_path.exists()
        assert artifact_path.suffix == f".{fmt}"
        assert artifact["format"] == fmt
        assert artifact["content_type"]
        assert artifact["download_url"] == f"/api/v1/artifacts/{artifact['artifact_id']}/download"


def test_create_artifact_rejects_unsupported_format(tmp_path):
    service = ArtifactService(base_dir=tmp_path)

    try:
        service.create_artifact(
            user_id="user-1",
            conversation_id="conv-1",
            task_id="task-1",
            title="报告",
            content="内容",
            artifact_format="pdf",
        )
    except ValueError as exc:
        assert "不支持的交付物格式" in str(exc)
    else:
        raise AssertionError("不支持的格式应该被拒绝")


def test_get_owned_artifact_rejects_other_user(tmp_path):
    service = ArtifactService(base_dir=tmp_path)
    artifact = service.create_markdown_artifact(
        user_id="user-1",
        conversation_id="conv-1",
        task_id="task-1",
        title="报告",
        content="内容",
    )

    try:
        service.get_owned_artifact(artifact["artifact_id"], "user-2")
    except PermissionError as exc:
        assert "无权访问" in str(exc)
    else:
        raise AssertionError("其他用户不应访问交付物")
