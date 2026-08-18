import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import HtmlPreviewFrame, { SANDBOX_BLACKLIST } from "../components/HtmlPreviewFrame";

describe("HtmlPreviewFrame T7 H1~H5", () => {
  it("H1 htmlContent=null → 显示 html-empty-hint", () => {
    render(<HtmlPreviewFrame htmlContent={null} />);
    const hint = screen.getByTestId("html-empty-hint");
    expect(hint).toBeTruthy();
    expect(hint.textContent).toContain("暂无 HTML 预览，请先生成报告");
  });

  it("H2 htmlContent='<h1>Hello</h1>' → iframe 存在且 sandbox=默认 allow-forms allow-downloads", () => {
    render(<HtmlPreviewFrame htmlContent="<h1>Hello</h1>" />);
    const iframe = screen.getByTestId("html-preview-iframe") as HTMLIFrameElement;
    expect(iframe).toBeTruthy();
    expect(iframe.getAttribute("sandbox")).toEqual("allow-forms allow-downloads");
  });

  it("H3 sandboxTokens 含 allow-scripts/allow-popups → 过滤后仅保留 allow-forms allow-downloads", () => {
    render(
      <HtmlPreviewFrame
        htmlContent="<p>x</p>"
        sandboxTokens={["allow-scripts", "allow-forms", "allow-popups", "allow-downloads"]}
      />
    );
    const iframe = screen.getByTestId("html-preview-iframe") as HTMLIFrameElement;
    expect(iframe.getAttribute("sandbox")).toEqual("allow-forms allow-downloads");
    const tokens = screen.getByTestId("html-sandbox-tokens");
    expect(tokens.textContent).toEqual("allow-forms allow-downloads");
  });

  it("H4 传入 6 blacklist 全集合 → sandbox='' 空字符串", () => {
    const allBlacklist = Array.from(SANDBOX_BLACKLIST);
    render(
      <HtmlPreviewFrame
        htmlContent="<p>x</p>"
        sandboxTokens={allBlacklist}
      />
    );
    const iframe = screen.getByTestId("html-preview-iframe") as HTMLIFrameElement;
    expect(iframe.getAttribute("sandbox")).toEqual("");
    const tokens = screen.getByTestId("html-sandbox-tokens");
    expect(tokens.textContent).toEqual("");
  });

  it("H5 csp 属性包含 default-src + referrerPolicy=no-referrer + loading=lazy", () => {
    render(<HtmlPreviewFrame htmlContent="<p>test</p>" />);
    const iframe = screen.getByTestId("html-preview-iframe") as HTMLIFrameElement;
    const csp = iframe.getAttribute("csp");
    expect(csp).toBeTruthy();
    expect(csp).toContain("default-src");
    expect(iframe.getAttribute("referrerpolicy")).toEqual("no-referrer");
    expect(iframe.getAttribute("loading")).toEqual("lazy");
  });
});
