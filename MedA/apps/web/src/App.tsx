import { useEffect, useState } from "react";

import { createClient, type ProjectSummary } from "@meda/shared-sdk";

export default function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  useEffect(() => {
    createClient().listProjects().then(setProjects);
  }, []);

  return (
    <main>
      <h1>MedA Web Shell</h1>
      <ul>
        {projects.map((project) => (
          <li key={project.id}>
            <strong>{project.name}</strong>
            <span>{project.workspace_key}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
