import { useEffect, useMemo, useState } from "react";

import {
  createBrowserSessionStore,
  createClient,
  type SessionContext,
} from "@meda/shared-sdk";

export default function App() {
  const sessionStore = useMemo(() => createBrowserSessionStore(), []);
  const client = useMemo(
    () => createClient("http://localhost:8000", sessionStore),
    [sessionStore],
  );
  const [session, setSession] = useState<SessionContext | null>(null);

  useEffect(() => {
    client
      .getMe()
      .then(setSession)
      .catch(() => setSession(null));
  }, [client]);

  if (session === null) {
    return <main>Admin session unavailable.</main>;
  }

  if (!["org_admin", "super_admin"].includes(session.role)) {
    return <main>Admin role required.</main>;
  }

  return (
    <main>
      <h1>MedA Admin Shell</h1>
      <p>{session.user.display_name}</p>
      <p>{session.organization.name}</p>
    </main>
  );
}
