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

  it("rejects adding an unknown key and strips any stray illegal keys from current", () => {
    expect(
      toggleKey(["pubmed", "fake", "embase", "bogus"], CATALOG_ORDER, "unknown"),
    ).toEqual(["pubmed", "embase"]);
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

  it("rejects trailing letters (strict 4-digit match)", () => {
    expect(parseYear("2024a")).toBeNull();
    expect(parseYear("2024abc")).toBeNull();
  });

  it("rejects shorter or longer than 4 digits", () => {
    expect(parseYear("24")).toBeNull();
    expect(parseYear("202")).toBeNull();
    expect(parseYear("20240")).toBeNull();
    expect(parseYear("20240")).toBeNull();
  });

  it("rejects signed numbers or punctuation", () => {
    expect(parseYear("+2024")).toBeNull();
    expect(parseYear("-2024")).toBeNull();
    expect(parseYear("2,024")).toBeNull();
  });

  it("clamps to plausible 1800-2100 range", () => {
    expect(parseYear("1799")).toBeNull();
    expect(parseYear("2101")).toBeNull();
    expect(parseYear("1800")).toBe(1800);
    expect(parseYear("2100")).toBe(2100);
    expect(parseYear("1985")).toBe(1985);
  });
});
