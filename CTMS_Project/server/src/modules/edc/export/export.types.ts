/**
 * 导出功能公共类型定义
 */

/**
 * 导出格式枚举（扩展性）
 */
export enum ExportFormat {
  SDTM = 'sdtm',
  ADAM = 'adam',
  ECRF = 'ecrf',
  SEND = 'send',
  CSV = 'csv',
  JSON = 'json',
  XPT = 'xpt'
}

/**
 * 导出请求参数（通用）
 */
export interface ExportRequest {
  format: ExportFormat;
  projectId: string;
  userId?: string;
  filters?: {
    startDate?: Date;
    endDate?: Date;
    domains?: string[];
    formIds?: string[];
  };
  fileName?: string;
}

/**
 * 日志审计条目
 */
export interface AuditLogEntry {
  timestamp: Date;
  userId: string;
  action: string;
  details: string;
  status: 'success' | 'failed';
}