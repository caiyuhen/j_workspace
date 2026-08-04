import { useMemo, useState } from "react";

import {
  createBrowserSessionStore,
  createClient,
  type ProjectSummary,
  type SessionContext,
} from "@meda/shared-sdk";

import { LoginForm } from "./components/LoginForm";
import { WorkspaceShell } from "./components/WorkspaceShell";

export default function App() {
  const sessionStore = useMemo(() => createBrowserSessionStore(), []);
  const client = useMemo(
    () => createClient("http://localhost:8000", sessionStore),
    [sessionStore],
  );
  const [session, setSession] = useState<SessionContext | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  const handleLogin = async (payload: {
    organizationSlug: string;
    userId: string;
  }) => {
    const nextSession = await client.devLogin({
      organization_slug: payload.organizationSlug,
      organization_name: "Demo Hospital",
      user_id: payload.userId,
      display_name: "Dr. Chen",
      role: "org_admin",
      client_type: "web",
    });
    const nextProjects = await client.listProjects();

    setSession(nextSession);
    setProjects(nextProjects);
  };

  if (session === null) {
    return <LoginForm onSubmit={handleLogin} />;
  }

  return <WorkspaceShell session={session} projects={projects} />;
}
