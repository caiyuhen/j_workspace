export type ProjectSummary = {
  id: number;
  name: string;
  workspace_key: string;
};

export function createClient(baseUrl = "http://localhost:8000") {
  return {
    async listProjects(): Promise<ProjectSummary[]> {
      const response = await fetch(`${baseUrl}/api/projects`);
      if (!response.ok) {
        return [];
      }

      return response.json();
    },
  };
}
