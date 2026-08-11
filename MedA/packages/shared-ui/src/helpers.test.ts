import { describe, expect, it } from "vitest";

import { parseYear, toggleKey } from "./SearchSourceConfigScreen";

const CATALOG_ORDER = ["pubmed", "embase", "cochrane", "wos", "cnki", "wanfang"];

describe("toggleKey", () => {
  it("adds a key following the catalog order", () => {
    expect(toggleKey(["pubmed"], CATALOG_ORDER, "cochrane")).toEqual([
      "pubmed",
      "cochrane",
    ]);
  });

  it("normalizes order when adding a key that sorts earlier", () => {
    expect(toggleKey(["cnki"], CATALOG_ORDER, "pubmed")).toEqual([
      "pubmed",
      "cnki",
    ]);
  });

  it("removes a key that is already selected", () => {
    expect(toggleKey(["pubmed", "embase"], CATALOG_ORDER, "embase")).toEqual([
      "pubmed",
    ]);
  });

  it("preserves relative order when removing", () => {
    expect(
      toggleKey(["pubmed", "cochrane", "cnki"], CATALOG_ORDER, "cochrane"),
    ).toEqual(["pubmed", "cnki"]);
  });

  it("returns a single key when toggling into an empty selection", () => {
    expect(toggleKey([], CATALOG_ORDER, "wos")).toEqual(["wos"]);
  });

  it("returns an empty array when removing the last key", () => {
    expect(toggleKey(["wos"], CATALOG_ORDER, "wos")).toEqual([]);
  });
});

describe("parseYear", () => {
  it("parses a numeric string", () => {
    expect(parseYear("2023")).toBe(2023);
  });

  it("returns null for an empty string", () => {
    expect(parseYear("")).toBeNull();
  });

  it("returns null for whitespace only", () => {
    expect(parseYear("   ")).toBeNull();
  });

  it("returns null for non-numeric text", () => {
    expect(parseYear("in press")).toBeNull();
  });

  it("ignores surrounding whitespace", () => {
    expect(parseYear("  2015  ")).toBe(2015);
  });
});
