// 数据质疑
export type QueryType = 'data_discrepancy' | 'missing_data' | 'protocol_deviation' | 'query clarification' | 'other';
export type QueryPriority = 'low' | 'medium' | 'high' | 'critical';
export type QueryAction = 'reply' | 'close' | 'escalate';

export interface DataQuery {
  id: string;
  projectId: string;
  subjectId?: string;
  formId?: string;
  fieldId?: string;
  queryType: QueryType;
  priority: QueryPriority;
  title: string;
  description: string;
  status: string;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateQueryParams {
  projectId: string;
  subjectId?: string;
  formId?: string;
  fieldId?: string;
  queryType: QueryType;
  priority?: QueryPriority;
  title: string;
  description: string;
  assignedTo?: string;
}

export interface ReplyQueryParams {
  content: string;
  action?: QueryAction;
}

export interface ReassignQueryParams {
  assignedTo: string;
  comment?: string;
}
