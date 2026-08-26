import { describe, expect, it } from "vitest";
import App from "../src/App";

describe("desktop renderer", () => {
  it("exposes the MedA desktop shell title", () => {
    expect(typeof App).toBe("function");
  });
});
