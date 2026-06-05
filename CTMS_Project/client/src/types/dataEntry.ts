// ==================== 数据录入 ====================

export interface VisitFormData {
  id: string;
  subjectId: string;
  visitId: string;
  formId: string;
  visitName?: string;
  formName?: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'verified' | 'locked' | 'query';
  data?: Record<string, any>;
  completedById?: string;
  completedAt?: string;
  verifiedById?: string;
  verifiedAt?: string;
  lockedAt?: string;
  changeCount: number;
  lastChangedAt?: string;
  createdAt: string;
  updatedAt: string;
  completedBy?: { id: string; displayName: string };
}

export interface FieldDefinition {
  fieldName: string;
  fieldLabel: string;
  fieldType: 'text' | 'number' | 'date' | 'select' | 'radio' | 'checkbox' | 'textarea';
  required: boolean;
  maxLength?: number;
  minValue?: number;
  maxValue?: number;
  options?: { value: string; label: string }[];
  validationRule?: string;
}

export interface ChangeHistory {
  id: string;
  formId: string;
  fieldName: string;
  oldValue: any;
  newValue: any;
  changedById: string;
  changedAt: string;
  reason: string;
  changedBy?: { id: string; displayName: string };
}

export interface DataEntrySummary {
  totalForms: number;
  completed: number;
  inProgress: number;
  notStarted: number;
  queried: number;
}
