// ==================== 审计日志 ====================

export interface AuditLog {
  id: string;
  userId: string;
  userName: string;
  eventType: string;
  tableName: string;
  recordId: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'LOGIN' | 'LOGOUT' | 'EXPORT' | 'SIGNATURE' | 'RANDOMIZE' | 'UNBLIND';
  oldValue?: Record<string, any>;
  newValue?: Record<string, any>;
  ipAddress: string;
  userAgent?: string;
  timestamp: string;
}

export interface AuditLogQuery {
  page?: number;
  pageSize?: number;
  eventType?: string;
  tableName?: string;
  action?: string;
  userId?: string;
  startDate?: string;
  endDate?: string;
  keyword?: string;
}

export interface AuditStats {
  totalEvents: number;
  todayEvents: number;
  byAction: { action: string; count: number }[];
  byEventType: { eventType: string; count: number }[];
  byUser: { userId: string; userName: string; count: number }[];
  dailyTrend: { date: string; count: number }[];
}

export interface RecordChange {
  id: string;
  auditLogId: string;
  tableName: string;
  recordId: string;
  fieldName: string;
  oldValue: any;
  newValue: any;
  changedById: string;
  changedByName: string;
  changedAt: string;
}
