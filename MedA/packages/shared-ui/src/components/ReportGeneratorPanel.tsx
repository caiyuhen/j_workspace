import React from "react";
import HtmlPreviewFrame from "./HtmlPreviewFrame";

export const HTTP_422_DETAIL_MAP: Record<string, string> = {
  grade_less_than_one: "GRADE 评估少于 1 项，请先至少完成一个结局指标的 GRADE 评估（推荐：关键结局必评 High/Moderate/Low/VeryLow）",
  prisma_less_than_five: "PRISMA 2020 勾选少于 5 项，请勾选 Protocol 部分的 5 项强制条目（第 1/2/3a/4/5 项）",
  forest_no_svg_content: "Meta 分析生成失败：森林图 SVG 为空，请先确认筛选阶段 ≥ 2 个研究、且二分类结局 RR/OR 设置正确",
  sof_no_grade_rows: "SoF 12 列表无任何 GRADE 行数据，请在 Stage 5 GRADE Tab 保存后再返回 Output 生成报告",
  no_evidences_selected: "证据抽取后 0 条符合条件，返回 Stage 4 Data Extraction 确认数据抽取标记 = include",
};

type ReportGeneratorPanelProps = {
  projectId: number;
  sha256?: string | null;
  versionLabel?: string | null;
  errorDetailLiteral?: string | null;
  activeTab: "editor" | "md" | "html";
  onActiveTabChange: (next: "editor" | "md" | "html") => void;
  editorSlot: React.ReactNode;
  mdPreviewSlot: string | null;
  htmlPreviewSlot?: string | null;
  onGenerateClick: () => void;
  onExportClick?: () => void;
  isGenerating?: boolean;
  isExporting?: boolean;
  generatedAt?: string | null;
  exportButtons?: Array<{label: string; onClick: () => void; testId?: string; variant?: "primary" | "ghost"}>;
};

function _formatShaDisplay(sha: string): string {
  const prefix = sha.slice(0, 12);
  const suffix = sha.slice(-4);
  if (sha.length <= 16) return sha;
  return `${prefix}...${suffix}`;
}

function _timeAgoLabel(iso: string | null | undefined): string | null {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return null;
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay}d ago`;
  } catch {
    return null;
  }
}

const panelBaseStyle: React.CSSProperties = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  display: "flex",
  flexDirection: "column",
  gap: "16px",
  fontFamily: "Inter, Arial, sans-serif",
  color: "#111827",
};

const titleRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: "16px",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "22px",
  fontWeight: 700,
  color: "#111827",
};

const shaRowStyle: React.CSSProperties = {
  marginTop: "8px",
  display: "flex",
  flexDirection: "column",
  gap: "4px",
  fontSize: "12px",
  color: "#6b7280",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
};

const shaValueStyle: React.CSSProperties = {
  fontSize: "11px",
  background: "#f3f4f6",
  padding: "2px 8px",
  borderRadius: "6px",
  display: "inline-block",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
};

const versionBadgeStyle: React.CSSProperties = {
  display: "inline-block",
  fontSize: "11px",
  padding: "2px 8px",
  borderRadius: "999px",
  background: "#eef2ff",
  color: "#3730a3",
  fontWeight: 600,
};

const errorBarStyle: React.CSSProperties = {
  padding: "12px 16px",
  borderRadius: "12px",
  background: "#fef2f2",
  border: "1px solid #fecaca",
  color: "#991b1b",
  fontSize: "13px",
  lineHeight: 1.6,
};

const tabBarStyle: React.CSSProperties = {
  display: "flex",
  gap: "4px",
  borderBottom: "1px solid #e5e7eb",
  marginBottom: "0",
};

const tabBtnStyle = (active: boolean): React.CSSProperties => ({
  padding: "10px 18px",
  borderRadius: "12px 12px 0 0",
  border: active ? "1px solid #c7d2fe" : "1px solid transparent",
  borderBottom: active ? "none" : undefined,
  background: active ? "#ffffff" : "transparent",
  color: active ? "#1e1b4b" : "#475569",
  fontWeight: active ? 700 : 500,
  fontSize: "14px",
  cursor: "pointer",
  ...(active ? {} : { opacity: 0.85 }),
});

const tabBodyStyle: React.CSSProperties = {
  border: "1px solid #e5e7eb",
  borderTop: "none",
  borderRadius: "0 0 16px 16px",
  minHeight: "320px",
  padding: "16px",
  background: "#fafbfc",
};

const mdPreStyle: React.CSSProperties = {
  margin: 0,
  padding: "16px",
  background: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: "10px",
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  fontSize: "13px",
  lineHeight: 1.6,
  color: "#1f2937",
  minHeight: "280px",
};

const actionRowStyle: React.CSSProperties = {
  display: "flex",
  gap: "12px",
  marginTop: "4px",
  flexWrap: "wrap",
  alignItems: "center",
};

const primaryBtnStyle = (disabled: boolean, loading: boolean): React.CSSProperties => ({
  padding: "10px 20px",
  borderRadius: "12px",
  border: "none",
  background: disabled ? "#9ca3af" : "#111827",
  color: "#f9fafb",
  fontWeight: 600,
  fontSize: "14px",
  cursor: disabled || loading ? "not-allowed" : "pointer",
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
  opacity: disabled ? 0.6 : 1,
});

const secondaryBtnStyle = (disabled: boolean, loading: boolean, ghost: boolean): React.CSSProperties => ({
  padding: "10px 18px",
  borderRadius: "12px",
  border: ghost ? "1px solid transparent" : "1px solid #d0d7e2",
  background: ghost ? "transparent" : "#ffffff",
  color: ghost ? "#374151" : "#111827",
  fontWeight: 500,
  fontSize: "14px",
  cursor: disabled || loading ? "not-allowed" : "pointer",
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  opacity: disabled ? 0.6 : 1,
});

const spinnerStyle: React.CSSProperties = {
  width: "14px",
  height: "14px",
  border: "2px solid rgba(255,255,255,0.3)",
  borderTopColor: "#ffffff",
  borderRadius: "50%",
  animation: "report-spin 0.6s linear infinite",
  display: "inline-block",
};

function Spinner(): JSX.Element {
  return (
    <>
      <style>{`@keyframes report-spin { to { transform: rotate(360deg); } }`}</style>
      <span data-testid="btn-spinner" aria-hidden="true" style={spinnerStyle} />
    </>
  );
}

export function ReportGeneratorPanel({
  projectId: _projectId,
  sha256,
  versionLabel,
  errorDetailLiteral,
  activeTab,
  onActiveTabChange,
  editorSlot,
  mdPreviewSlot,
  htmlPreviewSlot,
  onGenerateClick,
  onExportClick,
  isGenerating = false,
  isExporting = false,
  generatedAt,
  exportButtons = [],
}: ReportGeneratorPanelProps): JSX.Element {
  const errorText: string | null = errorDetailLiteral
    ? (HTTP_422_DETAIL_MAP[errorDetailLiteral] ?? errorDetailLiteral)
    : null;

  const timeAgo = _timeAgoLabel(generatedAt);

  return (
    <section style={panelBaseStyle}>
      <header style={titleRowStyle}>
        <div>
          <h2 style={titleStyle}>报告生成器</h2>
          {sha256 ? (
            <div style={shaRowStyle} data-testid="sha-row">
              <div>
                <span style={shaValueStyle} data-testid="sha-value">{_formatShaDisplay(sha256)}</span>
                {versionLabel ? (
                  <span style={{ ...versionBadgeStyle, marginLeft: "8px" }} data-testid="version-label">
                    {versionLabel}
                  </span>
                ) : null}
              </div>
              {timeAgo ? (
                <div data-testid="generated-at">生成于 {timeAgo}</div>
              ) : null}
            </div>
          ) : null}
        </div>
      </header>

      {errorText ? (
        <div data-testid="err-detail" style={errorBarStyle}>
          {errorText}
        </div>
      ) : null}

      <div style={tabBarStyle} role="tablist">
        <button
          type="button"
          role="tab"
          data-testid="tab-editor"
          aria-selected={activeTab === "editor"}
          style={tabBtnStyle(activeTab === "editor")}
          onClick={() => onActiveTabChange("editor")}
        >
          Editor 标签页
        </button>
        <button
          type="button"
          role="tab"
          data-testid="tab-md"
          aria-selected={activeTab === "md"}
          style={tabBtnStyle(activeTab === "md")}
          onClick={() => onActiveTabChange("md")}
        >
          Markdown 预览
        </button>
        <button
          type="button"
          role="tab"
          data-testid="tab-html"
          aria-selected={activeTab === "html"}
          style={tabBtnStyle(activeTab === "html")}
          onClick={() => onActiveTabChange("html")}
        >
          HTML 预览
        </button>
      </div>

      <div style={tabBodyStyle}>
        {activeTab === "editor" ? (
          <div data-testid="tab-body-editor">{editorSlot}</div>
        ) : activeTab === "md" ? (
          <pre data-testid="md-previewer" style={mdPreStyle}>
            {mdPreviewSlot ?? ""}
          </pre>
        ) : (
          <div data-testid="tab-body-html">
            <HtmlPreviewFrame htmlContent={htmlPreviewSlot ?? null} />
          </div>
        )}
      </div>

      <div style={actionRowStyle}>
        <button
          type="button"
          data-testid="btn-generate-report"
          disabled={isGenerating}
          aria-busy={isGenerating}
          style={primaryBtnStyle(isGenerating, isGenerating)}
          onClick={onGenerateClick}
        >
          {isGenerating ? <Spinner /> : null}
          {isGenerating ? "生成中…" : "生成报告"}
        </button>

        {onExportClick ? (
          <button
            type="button"
            data-testid="btn-export-report"
            disabled={isExporting || isGenerating}
            aria-busy={isExporting}
            style={secondaryBtnStyle(isExporting || isGenerating, isExporting, false)}
            onClick={onExportClick}
          >
            {isExporting ? <Spinner /> : null}
            {isExporting ? "导出中…" : "导出"}
          </button>
        ) : null}

        {exportButtons.map((eb, idx) => {
          const ghost = (eb.variant ?? "primary") === "ghost";
          const isPrimary = (eb.variant ?? "primary") === "primary";
          const style = isPrimary
            ? primaryBtnStyle(false, false)
            : secondaryBtnStyle(false, false, ghost);
          return (
            <button
              key={eb.testId ?? `eb-${idx}`}
              type="button"
              data-testid={eb.testId ?? undefined}
              style={style}
              onClick={eb.onClick}
            >
              {eb.label}
            </button>
          );
        })}
      </div>
    </section>
  );
}

export default ReportGeneratorPanel;
