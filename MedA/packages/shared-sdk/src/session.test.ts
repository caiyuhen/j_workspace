import { describe, expect, it } from "vitest";

import { createMemorySessionStore } from "./session";

describe("session store", () => {
  it("persists and clears bearer tokens", () => {
    const store = createMemorySessionStore();

    expect(store.getToken()).toBeNull();

    store.setToken("meda_token");
    expect(store.getToken()).toBe("meda_token");

    store.clearToken();
    expect(store.getToken()).toBeNull();
  });
});
