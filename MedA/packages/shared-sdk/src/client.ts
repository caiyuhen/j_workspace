import type { SessionStore } from "./session";
export { createBrowserSessionStore, createMemorySessionStore } from "./session";

export type ProjectSummary = {
  id: number;
  name: string;
  workspace_key: string;
};

export type SessionContext = {
  token: string;
  user: { user_id: string; display_name: string };
  organization: { slug: string; name: string };
  role: string;
  client_type: string;
};

export type DevLoginPayload = {
  organization_slug: string;
  organization_name: string;
  user_id: string;
  display_name: string;
  role: string;
  client_type: string;
};

export function createClient(
  baseUrl = "http://localhost:8000",
  sessionStore?: SessionStore,
) {
  const buildHeaders = () => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const token = sessionStore?.getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  };

  return {
    async devLogin(payload: DevLoginPayload): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/dev-login`, {
        method: "POST",
        headers: buildHeaders(),
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "login failed");
      }

      sessionStore?.setToken(data.token);
      return data;
    },

    async getMe(): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/me`, {
        headers: buildHeaders(),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "session bootstrap failed");
      }

      return data;
    },

    async listProjects(): Promise<ProjectSummary[]> {
      const response = await fetch(`${baseUrl}/api/projects`, {
        headers: buildHeaders(),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "project list failed");
      }

      return data;
    },
  };
}
