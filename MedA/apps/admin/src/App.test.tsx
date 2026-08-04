import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "./App";

vi.mock("@meda/shared-sdk", () => ({
  createBrowserSessionStore: () => ({ getToken: () => "meda_token" }),
  createClient: () => ({
    getMe: async () => ({
      token: "meda_token",
      user: { user_id: "u-001", display_name: "Ops Lead" },
      organization: { slug: "demo-hospital", name: "Demo Hospital" },
      role: "org_admin",
      client_type: "admin",
    }),
  }),
}));

test("admin app renders operator shell for admin role", async () => {
  render(<App />);

  expect(await screen.findByText("MedA Admin Shell")).toBeInTheDocument();
  expect(screen.getByText("Ops Lead")).toBeInTheDocument();
});
