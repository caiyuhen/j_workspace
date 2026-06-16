"""交付物生成与下载记录服务。"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


CONTENT_TYPES = {
    "md": "text/markdown; charset=utf-8",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


class ArtifactService:
    """管理任务交付物文件。"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or "deliverables").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts: Dict[str, Dict] = {}

    @staticmethod
    def _safe_title(title: str) -> str:
        title = (title or "交付物").strip()[:60]
        title = re.sub(r"[\\/:*?\"<>|\s]+", "_", title)
        return title.strip("_") or "交付物"

    @staticmethod
    def _plain_text(line: str) -> str:
        line = re.sub(r"^#{1,6}\s*", "", line.strip())
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        return line.strip()

    def _artifact_path(self, user_id: str, title: str, artifact_format: str) -> tuple[str, Path]:
        safe_title = self._safe_title(title)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_title}.{artifact_format}"
        user_dir = self.base_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return filename, user_dir / filename

    def _build_metadata(
        self,
        artifact_id: str,
        user_id: str,
        conversation_id: str,
        task_id: str,
        filename: str,
        path: Path,
        artifact_format: str,
    ) -> Dict:
        artifact = {
            "artifact_id": artifact_id,
            "task_id": task_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "filename": filename,
            "content_type": CONTENT_TYPES[artifact_format],
            "format": artifact_format,
            "path": str(path),
            "size": path.stat().st_size,
            "created_at": datetime.now(),
            "download_url": f"/api/v1/artifacts/{artifact_id}/download",
        }
        self._artifacts[artifact_id] = artifact
        return artifact

    def create_artifact(
        self,
        user_id: str,
        conversation_id: str,
        task_id: str,
        title: str,
        content: str,
        artifact_format: str = "md",
    ) -> Dict:
        """按指定格式创建交付物。"""
        artifact_format = (artifact_format or "md").lower()
        if artifact_format not in CONTENT_TYPES:
            raise ValueError(f"不支持的交付物格式: {artifact_format}")
        if artifact_format == "md":
            return self.create_markdown_artifact(user_id, conversation_id, task_id, title, content)

        artifact_id = str(uuid.uuid4())
        filename, path = self._artifact_path(user_id, title, artifact_format)
        if artifact_format == "docx":
            self._write_docx(path, title, content)
        elif artifact_format == "xlsx":
            self._write_xlsx(path, title, content)
        elif artifact_format == "pptx":
            self._write_pptx(path, title, content)
        return self._build_metadata(artifact_id, user_id, conversation_id, task_id, filename, path, artifact_format)

    def create_markdown_artifact(
        self,
        user_id: str,
        conversation_id: str,
        task_id: str,
        title: str,
        content: str,
    ) -> Dict:
        """保存 Markdown 交付物并返回可下载元数据。"""
        artifact_id = str(uuid.uuid4())
        filename, path = self._artifact_path(user_id, title, "md")
        path.write_text(content or "", encoding="utf-8")
        return self._build_metadata(artifact_id, user_id, conversation_id, task_id, filename, path, "md")

    def _write_docx(self, path: Path, title: str, content: str) -> None:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.shared import Pt

        doc = Document()
        styles = doc.styles
        styles["Normal"].font.name = "Arial"
        styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        styles["Normal"].font.size = Pt(11)
        doc.add_heading(self._plain_text(title), level=1)

        for line in (content or "").splitlines():
            raw = line.strip()
            if not raw:
                continue
            if raw.startswith("# "):
                doc.add_heading(self._plain_text(raw), level=1)
            elif raw.startswith("## "):
                doc.add_heading(self._plain_text(raw), level=2)
            elif raw.startswith("### "):
                doc.add_heading(self._plain_text(raw), level=3)
            elif raw.startswith(("- ", "* ")):
                doc.add_paragraph(self._plain_text(raw), style="List Bullet")
            elif raw.startswith("|") and raw.endswith("|"):
                doc.add_paragraph(self._plain_text(raw.replace("|", "  ")))
            else:
                doc.add_paragraph(self._plain_text(raw))
        doc.save(path)

    def _extract_table_rows(self, content: str) -> List[List[str]]:
        rows: List[List[str]] = []
        for line in (content or "").splitlines():
            raw = line.strip()
            if not (raw.startswith("|") and raw.endswith("|")):
                continue
            cells = [cell.strip() for cell in raw.strip("|").split("|")]
            if cells and not all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
                rows.append(cells)
        return rows

    def _write_xlsx(self, path: Path, title: str, content: str) -> None:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = "交付物"
        ws["A1"] = self._plain_text(title)
        ws["A1"].font = Font(bold=True, size=14)
        ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A1:D1")

        table_rows = self._extract_table_rows(content)
        if table_rows:
            start_row = 3
            for row_idx, row in enumerate(table_rows, start_row):
                for col_idx, value in enumerate(row, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=self._plain_text(value))
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
                    if row_idx == start_row:
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill("solid", fgColor="D9EAF7")
        else:
            row_idx = 3
            for line in (content or "").splitlines():
                text = self._plain_text(line)
                if text:
                    ws.cell(row=row_idx, column=1, value=text)
                    row_idx += 1

        for col_idx in range(1, ws.max_column + 1):
            letter = get_column_letter(col_idx)
            max_len = max(len(str(ws.cell(row=row_idx, column=col_idx).value or "")) for row_idx in range(1, ws.max_row + 1))
            ws.column_dimensions[letter].width = min(max_len + 4, 50)
        wb.save(path)

    def _write_pptx(self, path: Path, title: str, content: str) -> None:
        from pptx import Presentation
        from pptx.util import Pt

        prs = Presentation()
        title_slide = prs.slides.add_slide(prs.slide_layouts[0])
        title_slide.shapes.title.text = self._plain_text(title)
        title_slide.placeholders[1].text = "任务交付物"

        lines = [self._plain_text(line) for line in (content or "").splitlines() if self._plain_text(line)]
        chunks = [lines[i:i + 6] for i in range(0, len(lines), 6)] or [["暂无内容"]]
        for idx, chunk in enumerate(chunks[:12], 1):
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = chunk[0] if idx == 1 and len(chunk[0]) < 40 else f"第 {idx} 部分"
            body = slide.placeholders[1].text_frame
            body.clear()
            for item in chunk[:6]:
                p = body.add_paragraph()
                p.text = item[:120]
                p.font.size = Pt(18)
                p.level = 0
        prs.save(path)

    def get_owned_artifact(self, artifact_id: str, user_id: str) -> Dict:
        """获取当前用户拥有的交付物。"""
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise FileNotFoundError("交付物不存在")
        if artifact.get("user_id") != user_id:
            raise PermissionError("无权访问此交付物")
        path = Path(artifact["path"])
        if not path.exists() or not path.is_file():
            raise FileNotFoundError("交付物文件不存在或已被删除")
        return artifact


artifact_service = ArtifactService()
