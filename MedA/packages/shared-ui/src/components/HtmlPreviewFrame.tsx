import React from "react";

export const SANDBOX_BLACKLIST = new Set([
  "allow-scripts",
  "allow-same-origin",
  "allow-popups",
  "allow-top-navigation",
  "allow-top-navigation-by-user-activation",
  "allow-modals",
]);

const CSP_CONTENT =
  "default-src 'self' data: 'unsafe-inline'; img-src data: 'self'; media-src 'none'; object-src 'none'; base-uri 'none'; form-action 'self'; script-src 'none';";

type HtmlPreviewFrameProps = {
  htmlContent: string | null;
  title?: string;
  maxHeight?: string;
  className?: string;
  id?: string;
  sandboxTokens?: string[];
  _debugForceCspMeta?: boolean;
};

function _filterSandboxTokens(tokens: string[] | undefined): string[] {
  const base = tokens ?? ["allow-forms", "allow-downloads"];
  return base.filter((t) => !SANDBOX_BLACKLIST.has(t));
}

function _injectCspMetaIfNeeded(
  html: string | null | undefined,
  force: boolean | undefined
): string | undefined {
  if (!html) return undefined;
  if (!force) return html;
  const meta = `<meta http-equiv="Content-Security-Policy" content="${CSP_CONTENT}"/>`;
  if (/<head/i.test(html)) {
    return html.replace(/<head([^>]*)>/i, `<head$1>${meta}`);
  }
  return `${meta}${html}`;
}

export default function HtmlPreviewFrame({
  htmlContent,
  title,
  maxHeight = "70vh",
  className,
  id,
  sandboxTokens,
  _debugForceCspMeta,
}: HtmlPreviewFrameProps): JSX.Element {
  const filteredTokens = _filterSandboxTokens(sandboxTokens);
  const sandboxAttr = filteredTokens.length > 0 ? filteredTokens.join(" ") : "";
  const ariaLabel = title ?? "Report HTML preview";
  const srcDoc = _injectCspMetaIfNeeded(htmlContent, _debugForceCspMeta);

  if (!srcDoc) {
    return (
      <div
        className={className}
        id={id}
        data-testid="html-preview-frame-root"
        style={{ maxHeight, overflow: "auto", padding: "1rem" }}
      >
        <div data-testid="html-empty-hint">
          暂无 HTML 预览，请先生成报告
        </div>
      </div>
    );
  }

  return (
    <div
      className={className}
      id={id}
      data-testid="html-preview-frame-root"
      style={{ maxHeight, overflow: "auto" }}
    >
      <span data-testid="html-sandbox-tokens" style={{ display: "none" }}>
        {sandboxAttr}
      </span>
      <iframe
        data-testid="html-preview-iframe"
        title={ariaLabel}
        srcDoc={srcDoc}
        sandbox={sandboxAttr}
        referrerPolicy="no-referrer"
        loading="lazy"
        role="region"
        aria-label={ariaLabel}
        style={{ width: "100%", minHeight: "400px", border: "1px solid #e5e7eb", borderRadius: "0.5rem" }}
      />
    </div>
  );
}
