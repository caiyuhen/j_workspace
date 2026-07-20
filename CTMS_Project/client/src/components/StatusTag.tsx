import React from 'react';
import { Tag } from 'antd';

type StatusColorMap = Record<string, string>;

// 项目状态
const projectStatusMap: StatusColorMap = {
  planning: 'default',
  recruiting: 'processing',
  active: 'success',
  paused: 'warning',
  completed: 'green',
  terminated: 'error',
};

// 中心状态
const siteStatusMap: StatusColorMap = {
  active: 'success',
  inactive: 'default',
  suspended: 'warning',
  closed: 'error',
};

// 伦理/合同状态
const ethicsStatusMap: StatusColorMap = {
  pending: 'processing',
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
  under_review: 'processing',
  approved: 'success',
  conditionally_approved: 'warning',
  rejected: 'error',
  withdrawn: 'default',
=======
  approved: 'success',
  rejected: 'error',
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
  approved: 'success',
  rejected: 'error',
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
  approved: 'success',
  rejected: 'error',
>>>>>>> origin/main
  not_required: 'default',
};

// 受试者入组状态
const enrollmentStatusMap: StatusColorMap = {
  screening: 'processing',
  enrolled: 'blue',
  randomized: 'purple',
  ongoing: 'success',
  completed: 'green',
  discontinued: 'warning',
  withdrawn: 'error',
};

// 质疑优先级
const queryPriorityMap: StatusColorMap = {
  low: 'default',
  medium: 'processing',
  high: 'warning',
  critical: 'error',
};

// 质疑状态
const queryStatusMap: StatusColorMap = {
  open: 'processing',
  replied: 'blue',
  closed: 'success',
  escalated: 'warning',
};

// AE 严重程度
const severityMap: StatusColorMap = {
  mild: 'success',
  moderate: 'warning',
  severe: 'error',
};

// AE 严重性
const seriousnessMap: StatusColorMap = {
  non_serious: 'default',
  serious: 'error',
};

// 工作流状态
const workflowStatusMap: StatusColorMap = {
  pending: 'default',
  running: 'processing',
  approved: 'success',
  rejected: 'error',
  cancelled: 'warning',
};

// 工时状态
const timesheetStatusMap: StatusColorMap = {
  draft: 'default',
  submitted: 'processing',
  approved: 'success',
  rejected: 'error',
};

// 模板状态
const templateStatusMap: StatusColorMap = {
  draft: 'default',
  published: 'success',
  deprecated: 'warning',
  archived: 'default',
};

// 文档状态
const documentStatusMap: StatusColorMap = {
  draft: 'default',
  under_review: 'processing',
  pending_review: 'processing',
  approved: 'success',
  rejected: 'error',
  archived: 'warning',
  superseded: 'warning',
};

// 财务状态
const financeStatusMap: StatusColorMap = {
  draft: 'default',
  pending: 'processing',
  completed: 'success',
  cancelled: 'error',
};

// 供应商状态
const vendorStatusMap: StatusColorMap = {
  pending: 'processing',
  active: 'success',
  inactive: 'default',
  terminated: 'error',
};

// 药物状态
const drugStatusMap: StatusColorMap = {
  available: 'success',
  quarantined: 'warning',
  dispensed: 'processing',
  destroyed: 'error',
};

// 通用中文标签
const statusLabelMap: Record<string, Record<string, string>> = {
  project: { planning: '计划中', recruiting: '招募中', active: '进行中', paused: '暂停', completed: '已完成', terminated: '终止' },
  site: { active: '活跃', inactive: '停用', suspended: '暂停', closed: '关闭' },
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
  ethics: { pending: '待审批', under_review: '审查中', approved: '已批准', conditionally_approved: '附条件批准', rejected: '已拒绝', withdrawn: '已撤回', not_required: '不需要' },
=======
  ethics: { pending: '待审批', approved: '已批准', rejected: '已拒绝', not_required: '不需要' },
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
  ethics: { pending: '待审批', approved: '已批准', rejected: '已拒绝', not_required: '不需要' },
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
  ethics: { pending: '待审批', approved: '已批准', rejected: '已拒绝', not_required: '不需要' },
>>>>>>> origin/main
  contract: { pending: '待签署', signed: '已签署', terminated: '已终止' },
  enrollment: { screening: '筛选中', enrolled: '已入组', randomized: '已随机', ongoing: '进行中', completed: '已完成', discontinued: '退出', withdrawn: '撤回' },
  queryPriority: { low: '低', medium: '中', high: '高', critical: '紧急' },
  queryStatus: { open: '待回复', replied: '已回复', closed: '已关闭', escalated: '已升级' },
  severity: { mild: '轻度', moderate: '中度', severe: '重度' },
  seriousness: { non_serious: '非严重', serious: '严重' },
  workflow: { pending: '待处理', running: '进行中', approved: '已通过', rejected: '已拒绝', cancelled: '已取消' },
  timesheet: { draft: '草稿', submitted: '已提交', approved: '已批准', rejected: '已拒绝' },
  template: { draft: '草稿', published: '已发布', deprecated: '已停用', archived: '已归档' },
  document: { draft: '草稿', under_review: '审核中', pending_review: '待审核', approved: '已批准', rejected: '已拒绝', archived: '已归档', superseded: '已替代' },
  finance: { draft: '草稿', pending: '待处理', completed: '已完成', cancelled: '已取消' },
  vendor: { pending: '待审核', active: '活跃', inactive: '停用', terminated: '已终止' },
  drug: { available: '可用', quarantined: '隔离', dispensed: '已分发', destroyed: '已销毁' },
};

interface StatusTagProps {
  status?: string;
  category?: 'project' | 'site' | 'ethics' | 'contract' | 'enrollment' | 'queryPriority' | 'queryStatus' | 'severity' | 'seriousness' | 'workflow' | 'timesheet' | 'template' | 'document' | 'finance' | 'vendor' | 'drug';
  customColorMap?: StatusColorMap;
  customLabelMap?: Record<string, string>;
}

const colorMaps: Record<string, StatusColorMap> = {
  project: projectStatusMap,
  site: siteStatusMap,
  ethics: ethicsStatusMap,
  contract: ethicsStatusMap,
  enrollment: enrollmentStatusMap,
  queryPriority: queryPriorityMap,
  queryStatus: queryStatusMap,
  severity: severityMap,
  seriousness: seriousnessMap,
  workflow: workflowStatusMap,
  timesheet: timesheetStatusMap,
  template: templateStatusMap,
  document: documentStatusMap,
  finance: financeStatusMap,
  vendor: vendorStatusMap,
  drug: drugStatusMap,
};

const StatusTag: React.FC<StatusTagProps> = ({ status, category, customColorMap, customLabelMap }) => {
  if (!status) return null;

  const color = (customColorMap && customColorMap[status]) || (category ? colorMaps[category]?.[status] : 'default');
  const label = (customLabelMap && customLabelMap[status]) || (category ? statusLabelMap[category]?.[status] : status);

  return <Tag color={color}>{label || status}</Tag>;
};

export default StatusTag;
