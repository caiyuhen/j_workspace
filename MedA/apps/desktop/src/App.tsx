import { useEffect, useMemo, useState } from "react";

import {
  createClient,
  createMemorySessionStore,
  type ProjectSummary,
  type SessionContext,
} from "@meda/shared-sdk";

export default function App() {
  const sessionStore = useMemo(() => createMemorySessionStore("meda_token"), []);
  const client = useMemo(
    () => createClient("http://localhost:8000", sessionStore),
    [sessionStore],
  );
  const [session, setSession] = useState<SessionContext | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  useEffect(() => {
    client
      .getMe()
      .then(async (nextSession) => {
        setSession(nextSession);
        setProjects(await client.listProjects());
      })
      .catch(() => {
        setSession(null);
        setProjects([]);
      });
  }, [client]);

  if (session === null) {
    return <main>Desktop session unavailable.</main>;
  }

  return (
    <main>
      <h1>MedA Desktop Shell</h1>
      <p>{session.user.display_name}</p>
      <ul>
        {projects.map((project) => (
          <li key={project.id}>{project.name}</li>
        ))}
      </ul>
    </main>
  );
}
