import prisma from '../../config/database';
import { CreateMaskingRuleInput, UpdateMaskingRuleInput, PreviewMaskInput } from './masking.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { NotFoundError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

/** 脱敏处理函数 */
function applyMask(value: string, maskType: string, maskPattern?: string): string {
  if (!value) return value;

  switch (maskType) {
    case 'full':
      return '*'.repeat(value.length);
    case 'partial':
      if (value.length <= 2) return '**';
      return value[0] + '*'.repeat(value.length - 2) + value[value.length - 1];
    case 'hash':
      return value.substring(0, 4) + '****';
    case 'replace':
      return maskPattern || '***';
    case 'email': {
      const [local, domain] = value.split('@');
      if (!domain) return '***';
      return local[0] + '***@' + domain;
    }
    case 'phone':
      if (value.length >= 7) {
        return value.substring(0, 3) + '****' + value.substring(value.length - 4);
      }
      return '****';
    case 'id_card':
      if (value.length >= 8) {
        return value.substring(0, 4) + '********' + value.substring(value.length - 4);
      }
      return '****';
    default:
      return value;
  }
}

/** 自动检测字段可能需要的脱敏类型 */
function detectMaskType(fieldName: string, sampleValue?: string): string {
  const field = fieldName.toLowerCase();
  if (field.includes('password') || field.includes('secret') || field.includes('token')) return 'full';
  if (field.includes('email') || field.includes('mail')) return 'email';
  if (field.includes('phone') || field.includes('mobile') || field.includes('tel')) return 'phone';
  if (field.includes('id_card') || field.includes('idcard') || field.includes('identity') || field.includes('身份证')) return 'id_card';
  if (field.includes('name') && !field.includes('user')) return 'partial';
  return 'partial';
}

/** 常见敏感字段建议列表 */
const SENSITIVE_FIELD_SUGGESTIONS = [
  { tableName: 'users', fieldName: 'phone', suggestedType: 'phone' },
  { tableName: 'users', fieldName: 'email', suggestedType: 'email' },
  { tableName: 'subjects', fieldName: 'subjectCode', suggestedType: 'partial' },
  { tableName: 'users', fieldName: 'passwordHash', suggestedType: 'full' },
];

async function create(input: CreateMaskingRuleInput) {
  const rule = await prisma.dataMaskingRule.create({ data: input });
  logger.info('Masking rule created', { audit: true, eventType: 'MASKING_RULE_CREATE', ruleId: rule.id });
  return rule;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const where: any = {};
  if (query.tableName) where.tableName = query.tableName;
  if (query.maskType) where.maskType = query.maskType;

  const [rules, total] = await Promise.all([
    prisma.dataMaskingRule.findMany({ where, ...prismaPagination(pagination), orderBy: { createdAt: 'asc' } }),
    prisma.dataMaskingRule.count({ where }),
  ]);
  return buildPaginatedResult(rules, total, pagination);
}

async function getById(id: string) {
  const rule = await prisma.dataMaskingRule.findUnique({ where: { id } });
  if (!rule) throw new NotFoundError('DataMaskingRule', id);
  return rule;
}

async function update(id: string, input: UpdateMaskingRuleInput) {
  const rule = await prisma.dataMaskingRule.findUnique({ where: { id } });
  if (!rule) throw new NotFoundError('DataMaskingRule', id);
  return prisma.dataMaskingRule.update({ where: { id }, data: input });
}

async function remove(id: string) {
  const rule = await prisma.dataMaskingRule.findUnique({ where: { id } });
  if (!rule) throw new NotFoundError('DataMaskingRule', id);
  await prisma.dataMaskingRule.delete({ where: { id } });
  return { message: '脱敏规则已删除' };
}

/** 预览脱敏效果 */
async function preview(input: PreviewMaskInput) {
  const rule = await prisma.dataMaskingRule.findFirst({
    where: { tableName: input.tableName, fieldName: input.fieldName, isActive: true },
  });
  if (!rule) return { masked: input.value, rule: null, message: '无匹配的脱敏规则' };

  return {
    original: input.value,
    masked: applyMask(input.value, rule.maskType, rule.maskPattern || undefined),
    rule: { id: rule.id, maskType: rule.maskType },
  };
}

/** 对数据对象应用所有适用的脱敏规则 */
async function maskData(data: Record<string, any>, tableName: string): Promise<Record<string, any>> {
  const rules = await prisma.dataMaskingRule.findMany({
    where: { tableName, isActive: true },
  });
  if (rules.length === 0) return data;

  const masked = { ...data };
  for (const rule of rules) {
    if (masked[rule.fieldName] && typeof masked[rule.fieldName] === 'string') {
      masked[rule.fieldName] = applyMask(masked[rule.fieldName], rule.maskType, rule.maskPattern || undefined);
    }
  }
  return masked;
}

/** 批量脱敏 */
async function batchMask(records: Record<string, any>[], tableName: string): Promise<Record<string, any>[]> {
  const rules = await prisma.dataMaskingRule.findMany({
    where: { tableName, isActive: true },
  });
  if (rules.length === 0) return records;

  return records.map(record => {
    const masked = { ...record };
    for (const rule of rules) {
      if (masked[rule.fieldName] && typeof masked[rule.fieldName] === 'string') {
        masked[rule.fieldName] = applyMask(masked[rule.fieldName], rule.maskType, rule.maskPattern || undefined);
      }
    }
    return masked;
  });
}

/** 获取敏感字段建议 */
async function getSuggestions(tableName?: string) {
  let suggestions = [...SENSITIVE_FIELD_SUGGESTIONS];

  // 检查已有规则
  const existingRules = await prisma.dataMaskingRule.findMany({
    select: { tableName: true, fieldName: true },
  });
  const existingSet = new Set(existingRules.map(r => `${r.tableName}:${r.fieldName}`));

  // 过滤已配置的
  suggestions = suggestions.filter(s => !existingSet.has(`${s.tableName}:${s.fieldName}`));

  if (tableName) {
    suggestions = suggestions.filter(s => s.tableName === tableName);
  }

  return suggestions;
}

/** 获取脱敏规则统计 */
async function getStats() {
  const [total, active, byType, byTable] = await Promise.all([
    prisma.dataMaskingRule.count(),
    prisma.dataMaskingRule.count({ where: { isActive: true } }),
    prisma.dataMaskingRule.groupBy({ by: ['maskType'], _count: true }),
    prisma.dataMaskingRule.groupBy({ by: ['tableName'], _count: true }),
  ]);

  return {
    total,
    active,
    inactive: total - active,
    byType: byType.map(t => ({ maskType: t.maskType, count: t._count })),
    byTable: byTable.map(t => ({ tableName: t.tableName, count: t._count })),
  };
}

export const maskingService = {
  create, getList, getById, update, remove, preview, maskData,
  batchMask, getSuggestions, getStats,
};
