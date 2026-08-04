import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "./App";

const sessionStore = {
  getToken: vi.fn(() => null),
  setToken: vi.fn(),
  clearToken: vi.fn(),
};

const devLogin = vi.fn(async () => ({
  token: "meda_token",
  user: { user_id: "u-001", display_name: "Dr. Chen" },
  organization: { slug: "demo-hospital", name: "Demo Hospital" },
  role: "org_admin",
  client_type: "web",
}));

vi.mock("@meda/shared-sdk", () => ({
  createBrowserSessionStore: () => sessionStore,
  createClient: () => ({
    devLogin,
    listProjects: async () => [
      { id: 1, name: "糖尿病真实世界研究", workspace_key: "demo-hospital/糖尿病真实世界研究" },
    ],
    getMe: vi.fn(),
  }),
}));

test("web shell logs in and renders the protected workspace", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("机构标识"), {
    target: { value: "demo-hospital" },
  });
  fireEvent.change(screen.getByLabelText("用户编号"), {
    target: { value: "u-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));

  expect(await screen.findByText("欢迎，Dr. Chen")).toBeInTheDocument();
  expect(await screen.findByText("糖尿病真实世界研究")).toBeInTheDocument();
});
