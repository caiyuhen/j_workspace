// ==================== 系统设置 ====================

export interface User {
  id: string;
  username: string;
  displayName: string;
  email: string;
  phone?: string;
  department?: string;
  title?: string;
  roleId: string;
  status: 'active' | 'inactive' | 'locked';
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
  role?: Role;
}

export interface CreateUserParams {
  username: string;
  displayName: string;
  email: string;
  phone?: string;
  password: string;
  department?: string;
  title?: string;
  roleId?: string;
  roleIds?: string[];
}

export interface UpdateUserParams extends Partial<CreateUserParams> {
  status?: 'active' | 'inactive' | 'locked';
}

export interface Role {
  id: string;
  name: string;
  code: string;
  description?: string;
  permissions: string[];
  userCount?: number;
  isSystem: boolean;
  createdAt: string;
}

export interface CreateRoleParams {
  name: string;
  code: string;
  description?: string;
  permissions: string[];
}

export interface Organization {
  id: string;
  name: string;
  code: string;
  type: 'sponsor' | 'cro' | 'site' | 'vendor' | 'regulatory' | 'other';
  parentId?: string;
  address?: string;
  contactPerson?: string;
  contactPhone?: string;
  contactEmail?: string;
  status: 'active' | 'inactive';
  createdAt: string;
  gcpContactName?: string;
  gcpContactPhone?: string;
  researchContactName?: string;
  researchContactPhone?: string;
  investigatorName?: string;
}

export interface NotificationConfig {
  id: string;
  channel: 'wechat_work' | 'email' | 'sms' | 'in_app';
  eventType: string;
  templateId?: string;
  enabled: boolean;
  recipients?: string[];
}

export interface SystemConfig {
  key: string;
  value: string;
  description?: string;
  category: string;
  updatedAt: string;
}
