import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "../src/App";

vi.mock("@meda/shared-sdk", () => ({
  createMemorySessionStore: () => ({ getToken: () => "meda_token" }),
  createClient: () => ({
    getMe: async () => ({
      token: "meda_token",
      user: { user_id: "u-001", display_name: "Dr. Chen" },
      organization: { slug: "demo-hospital", name: "Demo Hospital" },
      role: "researcher",
      client_type: "desktop",
    }),
    listProjects: async () => [
      {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
      },
    ],
  }),
}));

test("desktop app renders authenticated workspace shell", async () => {
  render(<App />);

  expect(await screen.findByText("MedA Desktop Shell")).toBeInTheDocument();
  expect(screen.getByText("糖尿病真实世界研究")).toBeInTheDocument();
});
