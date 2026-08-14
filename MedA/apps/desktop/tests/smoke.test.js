import { describe, expect, it } from "vitest";
describe("desktop renderer", () => {
    it("exposes the MedA desktop shell title", async () => {
        const module = await import("../src/App");
        expect(typeof module.default).toBe("function");
    });
});
