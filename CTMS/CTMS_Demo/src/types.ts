
export interface Task {
  id: string;
  title: string;
  description: string;
  ctmsSupport?: string;
  gcpReference?: string;
  requiredDocs?: string[];
}

export interface RoleStageData {
  roleId: string;
  stageId: string;
  tasks: Task[];
  keyFocus: string; // GCP Key Focus
}
