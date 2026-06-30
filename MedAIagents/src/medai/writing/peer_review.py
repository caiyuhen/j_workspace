"""
同行评审辅助模块 (v0.4.0)
Peer Review Assistant Module

功能:
- 审稿意见智能分类与解析
- 逐条回复模板生成
- Response Letter 结构化撰写
- 修改痕迹对比与总结
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ReviewCommentType(Enum):
    """审稿意见类型"""
    MAJOR_CONCERN = "Major Concern (重大问题)"
    MINOR_COMMENT = "Minor Comment (次要意见)"
    METHODOLOGY = "Methodology (方法学)"
    STATISTICS = "Statistics (统计学)"
    LANGUAGE = "Language (语言/写作)"
    ETHICS = "Ethics (伦理)"
    SUGGESTION = "Suggestion (建议)"
    CLARIFICATION = "Clarification (澄清)"
    GENERAL = "General (一般性)"


class ResponseStrategy(Enum):
    """回复策略"""
    ACCEPT = "接受意见，已修改"
    PARTIAL = "部分接受，已调整"
    DISAGREE = "保留观点，已说明理由"
    CLARIFY = "澄清误解，已解释"
    THANK = "感谢建议，已考虑"


@dataclass
class ReviewComment:
    """单条审稿意见"""
    reviewer_id: str
    comment_id: str
    original_text: str
    comment_type: ReviewCommentType
    severity: int = 1  # 1-5, 5最严重
    location: str = ""  # 涉及的章节
    line_numbers: Optional[str] = None
    suggested_change: str = ""


@dataclass
class AuthorResponse:
    """作者回复"""
    comment_id: str
    response_strategy: ResponseStrategy
    response_text: str
    changes_made: str = ""  # 具体修改内容
    page_line_reference: str = ""  # 修改位置


class ReviewCommentParser:
    """审稿意见解析器"""

    TYPE_KEYWORDS = {
        ReviewCommentType.MAJOR_CONCERN: [
            "major", "concern", "significant", "fundamental", "critical",
            "重大", "严重", "根本", "关键", "主要问题"
        ],
        ReviewCommentType.MINOR_COMMENT: [
            "minor", "small", "trivial", "slight",
            "次要", "小", "轻微", "细节"
        ],
        ReviewCommentType.METHODOLOGY: [
            "method", "design", "protocol", "approach", "experimental",
            "方法", "设计", "方案", "实验", "protocol"
        ],
        ReviewCommentType.STATISTICS: [
            "statistical", "statistics", "p-value", "significance", "power", "sample size",
            "统计", "样本量", "检验效能", "显著性"
        ],
        ReviewCommentType.LANGUAGE: [
            "language", "grammar", "spelling", "typo", "writing", "english",
            "语言", "语法", "拼写", "写作", "表达"
        ],
        ReviewCommentType.ETHICS: [
            "ethic", "consent", "irb", "approval",
            "伦理", "知情同意", "伦理委员会"
        ],
        ReviewCommentType.SUGGESTION: [
            "suggest", "recommend", "consider", "might", "could",
            "建议", "推荐", "考虑"
        ],
        ReviewCommentType.CLARIFICATION: [
            "clarify", "unclear", "confused", "question",
            "澄清", "不清楚", "疑问", "困惑"
        ],
    }

    def parse_comments(self, review_text: str, reviewer_id: str = "Reviewer") -> List[ReviewComment]:
        """
        解析审稿意见文本
        """
        comments = []

        # 尝试按编号分割 (1. 2. 3. 或 Comment 1: 等)
        patterns = [
            r'(?:\n|^)\s*(?:\d+\.|Comment\s*\d+[:：]|Point\s*\d+[:：])\s*',
            r'(?:\n|^)\s*(?:Major\s+\d+[:：]|Minor\s+\d+[:：])\s*',
        ]

        sections = []
        for pattern in patterns:
            parts = re.split(pattern, review_text)
            if len(parts) > 2:
                sections = [p.strip() for p in parts if len(p.strip()) > 10]
                break

        if not sections:
            # 无法分割，将整个文本作为一条意见
            sections = [review_text.strip()]

        for i, section in enumerate(sections, 1):
            comment_type = self._classify_comment(section)
            severity = self._assess_severity(section, comment_type)
            location = self._extract_location(section)

            comments.append(ReviewComment(
                reviewer_id=reviewer_id,
                comment_id=f"{reviewer_id}_C{i:02d}",
                original_text=section[:500],
                comment_type=comment_type,
                severity=severity,
                location=location,
            ))

        return comments

    def _classify_comment(self, text: str) -> ReviewCommentType:
        """分类审稿意见"""
        text_lower = text.lower()
        scores = {}

        for ctype, keywords in self.TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                scores[ctype] = score

        if scores:
            return max(scores, key=scores.get)
        return ReviewCommentType.GENERAL

    def _assess_severity(self, text: str, ctype: ReviewCommentType) -> int:
        """评估严重程度"""
        text_lower = text.lower()

        if ctype == ReviewCommentType.MAJOR_CONCERN:
            return 5
        if ctype == ReviewCommentType.ETHICS:
            return 5
        if ctype == ReviewCommentType.METHODOLOGY:
            return 4
        if ctype == ReviewCommentType.STATISTICS:
            return 4
        if ctype == ReviewCommentType.MINOR_COMMENT:
            return 2
        if ctype == ReviewCommentType.LANGUAGE:
            return 1

        # 根据关键词进一步判断
        severe_words = ["must", "essential", "required", "necessary", "cannot",
                        "必须", "必要", "要求", "不能"]
        if any(w in text_lower for w in severe_words):
            return 4

        return 3

    def _extract_location(self, text: str) -> str:
        """提取涉及的章节位置"""
        text_lower = text.lower()
        locations = []

        loc_keywords = {
            "Abstract": ["abstract", "摘要"],
            "Introduction": ["introduction", "背景", "前言"],
            "Methods": ["methods", "methodology", "方法"],
            "Results": ["results", "结果"],
            "Discussion": ["discussion", "讨论"],
            "Conclusion": ["conclusion", "结论"],
            "Table/Figure": ["table", "figure", "表", "图"],
            "Reference": ["reference", "文献"],
        }

        for loc, kws in loc_keywords.items():
            if any(kw in text_lower for kw in kws):
                locations.append(loc)

        return ", ".join(locations) if locations else "全文"

    def summarize_review(self, comments: List[ReviewComment]) -> Dict[str, Any]:
        """汇总审稿意见统计"""
        total = len(comments)
        type_counts = {}
        severity_sum = 0

        for c in comments:
            type_counts[c.comment_type.value] = type_counts.get(c.comment_type.value, 0) + 1
            severity_sum += c.severity

        avg_severity = severity_sum / total if total > 0 else 0
        major_count = sum(1 for c in comments if c.severity >= 4)

        return {
            "total_comments": total,
            "major_concerns": major_count,
            "minor_comments": total - major_count,
            "average_severity": round(avg_severity, 1),
            "type_distribution": type_counts,
            "requires_major_revision": major_count > 0,
            "priority_issues": [c.original_text[:80] + "..."
                               for c in comments if c.severity >= 4]
        }


class ResponseGenerator:
    """回复生成器"""

    TEMPLATES = {
        (ReviewCommentType.METHODOLOGY, ResponseStrategy.ACCEPT): """
感谢审稿人的宝贵意见。我们已按照建议对研究方法进行了修改。

具体修改如下：
{changes}

修改后的内容位于稿件第{location}页。修改后的方法学描述更加清晰完整。
        """,
        (ReviewCommentType.STATISTICS, ResponseStrategy.ACCEPT): """
感谢审稿人对统计分析提出的专业意见。我们已重新审视并修正了统计分析方案。

修改内容：
{changes}

修正后的统计方法描述请见稿件第{location}页的"统计方法"部分。
        """,
        (ReviewCommentType.LANGUAGE, ResponseStrategy.ACCEPT): """
感谢审稿人的指正。我们已仔细修改了相关段落的语言表达，并请英语母语人士进行了润色。

修改位置：{location}

修改后的表述更加准确流畅。
        """,
        (ReviewCommentType.SUGGESTION, ResponseStrategy.THANK): """
感谢审稿人的建设性建议。虽然受限于本研究的范围和数据，我们无法在本次修改中完全采纳该建议，但我们已在"讨论"部分的"研究局限性"中明确提及了这一点，并提出了未来研究的方向。

具体请见稿件第{location}页。
        """,
        (ReviewCommentType.CLARIFICATION, ResponseStrategy.CLARIFY): """
感谢审稿人的提问，这确实需要进一步说明。

{changes}

我们已在稿件第{location}页补充了相关解释，以使表述更加清晰。
        """,
        (ReviewCommentType.MAJOR_CONCERN, ResponseStrategy.ACCEPT): """
我们非常感谢审稿人提出的这一重要问题。这确实是本研究需要认真回应的核心问题。

经过深入讨论和补充分析，我们已按以下方式进行了修改：

{changes}

我们相信这些修改充分回应了审稿人的关切，并使研究结论更加可靠。修改内容详见稿件第{location}页。
        """,
        (ReviewCommentType.MAJOR_CONCERN, ResponseStrategy.DISAGREE): """
感谢审稿人提出的深刻见解。我们非常重视这一问题，并对原数据进行了重新审视。

经过反复核实，我们认为：

{changes}

虽然与审稿人的观点存在差异，但我们希望上述解释能够说明我们保留原结论的合理性。如果审稿人认为有必要，我们愿意在讨论中增加一段关于该问题的辩论性讨论。
        """,
    }

    def generate_response(self,
                         comment: ReviewComment,
                         strategy: ResponseStrategy,
                         changes: str = "",
                         location: str = "X") -> AuthorResponse:
        """
        生成单条回复
        """
        key = (comment.comment_type, strategy)

        if key in self.TEMPLATES:
            template = self.TEMPLATES[key]
        else:
            # 通用模板
            strategy_texts = {
                ResponseStrategy.ACCEPT: "我们已按照审稿意见进行了修改。",
                ResponseStrategy.PARTIAL: "我们已部分采纳审稿意见并进行了相应调整。",
                ResponseStrategy.DISAGREE: "经过慎重考虑，我们保留了原有观点，理由如下：",
                ResponseStrategy.CLARIFY: "感谢提问，现澄清如下：",
                ResponseStrategy.THANK: "感谢建议，我们已认真考虑。",
            }
            template = f"""
{strategy_texts.get(strategy, '感谢审稿人的意见。')}

{changes}

修改位置：稿件第{location}页。
            """

        response_text = template.format(changes=changes, location=location).strip()

        return AuthorResponse(
            comment_id=comment.comment_id,
            response_strategy=strategy,
            response_text=response_text,
            changes_made=changes,
            page_line_reference=location,
        )

    def suggest_strategy(self, comment: ReviewComment) -> ResponseStrategy:
        """根据意见类型推荐回复策略"""
        if comment.comment_type == ReviewCommentType.MAJOR_CONCERN:
            return ResponseStrategy.ACCEPT
        if comment.comment_type == ReviewCommentType.METHODOLOGY:
            return ResponseStrategy.ACCEPT
        if comment.comment_type == ReviewCommentType.STATISTICS:
            return ResponseStrategy.ACCEPT
        if comment.comment_type == ReviewCommentType.ETHICS:
            return ResponseStrategy.ACCEPT
        if comment.comment_type == ReviewCommentType.LANGUAGE:
            return ResponseStrategy.ACCEPT
        if comment.comment_type == ReviewCommentType.CLARIFICATION:
            return ResponseStrategy.CLARIFY
        if comment.comment_type == ReviewCommentType.SUGGESTION:
            return ResponseStrategy.THANK
        return ResponseStrategy.ACCEPT


class ResponseLetterWriter:
    """Response Letter 撰写器"""

    def __init__(self):
        self.parser = ReviewCommentParser()
        self.generator = ResponseGenerator()

    def write_response_letter(self,
                              reviewer_comments: Dict[str, str],
                              manuscript_id: str = "",
                              title: str = "",
                              authors: str = "",
                              custom_responses: Dict[str, Tuple[ResponseStrategy, str]] = None) -> str:
        """
        生成完整的 Response Letter

        Args:
            reviewer_comments: {reviewer_id: comment_text}
            manuscript_id: 稿件编号
            title: 论文标题
            authors: 作者信息
            custom_responses: 自定义回复 {comment_id: (strategy, changes)}

        Returns:
            完整的 Response Letter 文本
        """
        custom_responses = custom_responses or {}

        letter = f"""
Dear Editor,

Thank you for giving us the opportunity to revise our manuscript
"{title}" (Manuscript ID: {manuscript_id}).

We have carefully considered all the comments from the reviewers and
have made substantial revisions accordingly. Below, we provide a
point-by-point response to each comment. All changes in the revised
manuscript are highlighted in yellow.

{'='*60}
"""

        for reviewer_id, comment_text in reviewer_comments.items():
            letter += f"\n\n{'='*60}\n"
            letter += f"Response to {reviewer_id}\n"
            letter += f"{'='*60}\n"

            comments = self.parser.parse_comments(comment_text, reviewer_id)
            summary = self.parser.summarize_review(comments)

            letter += f"\nSummary: {summary['total_comments']} comments "
            letter += f"({summary['major_concerns']} major, {summary['minor_comments']} minor)\n\n"

            for comment in comments:
                letter += f"\n---\n\n"
                letter += f"Comment {comment.comment_id} [{comment.comment_type.value}]\n"
                letter += f"Location: {comment.location}\n"
                letter += f"Severity: {'★' * comment.severity}{'☆' * (5 - comment.severity)}\n\n"
                letter += f"Reviewer: {comment.original_text[:200]}\n\n"

                # 使用自定义回复或生成默认回复
                if comment.comment_id in custom_responses:
                    strategy, changes = custom_responses[comment.comment_id]
                else:
                    strategy = self.generator.suggest_strategy(comment)
                    changes = "[请在此处填写具体修改内容]"

                response = self.generator.generate_response(
                    comment, strategy, changes, "XX"
                )

                letter += f"Response:\n{response.response_text}\n"

        letter += f"""

{'='*60}

We hope that the revisions adequately address all the reviewers' concerns.
Please do not hesitate to contact us if any further clarification is needed.

Sincerely,
{authors}

{'='*60}
"""
        return letter

    def generate_quick_response(self, comment_text: str) -> str:
        """快速生成回复建议"""
        comments = self.parser.parse_comments(comment_text, "Reviewer")
        responses = []

        for comment in comments:
            strategy = self.generator.suggest_strategy(comment)
            response = self.generator.generate_response(
                comment, strategy, "[待补充具体修改]", "XX"
            )
            responses.append({
                "type": comment.comment_type.value,
                "original": comment.original_text[:100] + "...",
                "suggested_strategy": strategy.value,
                "draft_response": response.response_text[:200] + "..."
            })

        return responses


class RevisionTracker:
    """修改痕迹追踪器"""

    def __init__(self):
        self.revisions = []

    def add_revision(self,
                     comment_id: str,
                     location: str,
                     original_text: str,
                     revised_text: str,
                     reason: str = ""):
        """添加修改记录"""
        self.revisions.append({
            "comment_id": comment_id,
            "location": location,
            "original": original_text,
            "revised": revised_text,
            "change_type": self._classify_change(original_text, revised_text),
            "reason": reason,
        })

    def _classify_change(self, original: str, revised: str) -> str:
        """分类修改类型"""
        if not original:
            return "新增"
        if not revised:
            return "删除"
        if len(revised) > len(original) * 1.5:
            return "大幅扩充"
        if len(revised) < len(original) * 0.7:
            return "精简"
        return "修改"

    def generate_revision_summary(self) -> str:
        """生成修改总结表"""
        if not self.revisions:
            return "暂无修改记录"

        type_counts = {}
        for r in self.revisions:
            ctype = r["change_type"]
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

        summary = f"""
{'='*60}
修改痕迹总结表
{'='*60}

总修改数: {len(self.revisions)}

修改类型分布:
"""
        for ctype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            summary += f"  • {ctype}: {count} 处\n"

        summary += f"""
{'='*60}
详细修改列表:
{'='*60}
"""
        for i, r in enumerate(self.revisions, 1):
            summary += f"""
[{i}] Comment: {r['comment_id']} | Location: {r['location']} | Type: {r['change_type']}
  原文: {r['original'][:100]}{'...' if len(r['original']) > 100 else ''}
  修改: {r['revised'][:100]}{'...' if len(r['revised']) > 100 else ''}
  原因: {r['reason'][:80]}{'...' if len(r['reason']) > 80 else ''}
"""

        return summary

    def export_change_log(self) -> List[Dict[str, str]]:
        """导出修改日志"""
        return self.revisions


class PeerReviewAssistant:
    """同行评审辅助主类"""

    def __init__(self):
        self.parser = ReviewCommentParser()
        self.generator = ResponseGenerator()
        self.writer = ResponseLetterWriter()
        self.tracker = RevisionTracker()

    def analyze_review(self, review_text: str, reviewer_id: str = "Reviewer") -> Dict[str, Any]:
        """
        完整分析审稿意见
        """
        comments = self.parser.parse_comments(review_text, reviewer_id)
        summary = self.parser.summarize_review(comments)

        # 为每条意见生成建议回复
        suggested_responses = []
        for comment in comments:
            strategy = self.generator.suggest_strategy(comment)
            response = self.generator.generate_response(
                comment, strategy, "[待补充]", "XX"
            )
            suggested_responses.append({
                "comment_id": comment.comment_id,
                "type": comment.comment_type.value,
                "severity": comment.severity,
                "suggested_strategy": strategy.value,
                "draft_response": response.response_text,
            })

        return {
            "summary": summary,
            "comments": comments,
            "suggested_responses": suggested_responses,
            "revision_needed": summary["requires_major_revision"],
            "estimated_hours": len(comments) * 2 + summary["major_concerns"] * 4,
        }
