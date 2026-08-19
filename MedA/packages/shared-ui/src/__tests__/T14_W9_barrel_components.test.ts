import { describe, it, expect } from "vitest";
import * as SharedUI from "../index";

describe("T14 W9 Barrel Component+Hook Exports (5)", () => {
  it("T14-C1: imports 5 names non-undefined via barrel index", () => {
    expect(SharedUI.FunnelProgressBar, "FunnelProgressBar undefined via barrel").toBeDefined();
    expect(SharedUI.RoB2Matrix, "RoB2Matrix undefined via barrel").toBeDefined();
    expect(SharedUI.AbstractorCard, "AbstractorCard undefined via barrel").toBeDefined();
    expect(SharedUI.ConfidenceBar, "ConfidenceBar undefined via barrel").toBeDefined();
    expect(SharedUI.useEvidenceArtifact, "useEvidenceArtifact undefined via barrel").toBeDefined();
  });

  it("T14-C2: 3 components typeof === function (React FC), 1 hook typeof === function", () => {
    expect(typeof SharedUI.FunnelProgressBar === "function").toBe(true);
    expect(typeof SharedUI.RoB2Matrix === "function").toBe(true);
    expect(typeof SharedUI.AbstractorCard === "function").toBe(true);
    expect(typeof SharedUI.ConfidenceBar === "function").toBe(true);
    expect(typeof SharedUI.useEvidenceArtifact === "function").toBe(true);
  });

  it("T14-C3: 5 PascalCase/camelCase names exist on barrel object keys", () => {
    const keys = Object.keys(SharedUI);
    expect(keys.includes("FunnelProgressBar")).toBe(true);
    expect(keys.includes("RoB2Matrix")).toBe(true);
    expect(keys.includes("AbstractorCard")).toBe(true);
    expect(keys.includes("ConfidenceBar")).toBe(true);
    expect(keys.includes("useEvidenceArtifact")).toBe(true);
  });
});
