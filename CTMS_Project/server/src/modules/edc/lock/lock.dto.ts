// lock.dto.ts - 数据锁定管理数据传输对象

export interface CreateLockDto {
  projectId: string;
  lockType: string;        // 'subject' | 'visit' | 'project' | 'form'
  targetId: string;        // 对应 subject/visit/project/form 的 ID
  lockReason?: string;
  esigRecords?: Record<string, any>;
}

export interface UnlockDto {
  unlockApprovedBy?: string;
  unlockReason?: string;
}

export interface LockQueryDto {
  projectId?: string;
  lockType?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}
