// 工作流
export type WorkflowType = 'project_approval' | 'site_activation' | 'budget_review' | 'protocol_amendment' | 'safety_report' | 'data_lock' | 'contract_approval' | 'other';
export type NodeType = 'submit' | 'review' | 'approve' | 'authorize' | 'inform' | 'complete';
export type WorkflowAction = 'approve' | 'reject' | 'delegate' | 'return' | 'countersign';
export type CountersignPassMode = 'all' | 'majority' | 'one';

export interface WorkflowStage {
  id: string;
  name: string;
  approverRole: string;
  nodeType?: NodeType;
  esigRequired?: boolean;
  esigDualSign?: boolean;
  timeoutDays?: number;
  timeoutHours?: number;
  isCountersign?: boolean;
  countersignApprovers?: string[];
  countersignPassMode?: CountersignPassMode;
  allowReturn?: boolean;
  returnToStageIds?: string[];
}

export interface WorkflowDefinition {
  id: string;
  workflowCode: string;
  workflowName: string;
  workflowType: WorkflowType;
  stages: WorkflowStage[];
  description?: string;
  allowDelegate?: boolean;
  notificationEnabled?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateDefinitionParams {
  workflowCode: string;
  workflowName: string;
  workflowType: WorkflowType;
  stages: WorkflowStage[];
  description?: string;
  allowDelegate?: boolean;
  notificationEnabled?: boolean;
}

// 流程实例
export interface WorkflowInstance {
  id: string;
  definitionId: string;
  workflowType?: string;
  projectId?: string;
  status: string;
  currentStageId?: string;
  currentStageName?: string;
  businessData?: Record<string, any>;
  createdAt: string;
}

export interface StartInstanceParams {
  definitionId: string;
  workflowType?: string;
  projectId?: string;
  businessData?: Record<string, any>;
  initiatorComment?: string;
}

export interface ProcessTaskParams {
  action: WorkflowAction;
  comment?: string;
  delegateTo?: string;
  returnToStageId?: string;
  esigData?: {
    signatureMeaning: string;
    signatureReason: string;
  };
  esigDataSecondary?: {
    signatureMeaning: string;
    signatureReason: string;
  };
}

// 待办任务
export interface WorkflowTask {
  id: string;
  instanceId: string;
  instance: WorkflowInstance;
  taskId: string;
  stageName: string;
  stageId: string;
  assigneeId: string;
  status: string;
  createdAt: string;
}
