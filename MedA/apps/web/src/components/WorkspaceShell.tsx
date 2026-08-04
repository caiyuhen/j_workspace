import type { ProjectSummary, SessionContext } from "@meda/shared-sdk";

type WorkspaceShellProps = {
  session: SessionContext;
  projects: ProjectSummary[];
};

export function WorkspaceShell({ session, projects }: WorkspaceShellProps) {
  return (
    <main>
      <h1>欢迎，{session.user.display_name}</h1>
      <p>
        当前机构：{session.organization.name} ({session.organization.slug})
      </p>
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
