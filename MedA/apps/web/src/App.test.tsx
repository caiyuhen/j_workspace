import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "./App";

vi.mock("@meda/shared-sdk", () => ({
  createClient: () => ({
    listProjects: async () => [
      { id: 1, name: "糖尿病真实世界研究", workspace_key: "demo-hospital/糖尿病真实世界研究" },
    ],
  }),
}));

test("web shell renders project workspace cards", async () => {
  render(<App />);

  expect(await screen.findByText("糖尿病真实世界研究")).toBeInTheDocument();
  expect(screen.getByText("demo-hospital/糖尿病真实世界研究")).toBeInTheDocument();
});
