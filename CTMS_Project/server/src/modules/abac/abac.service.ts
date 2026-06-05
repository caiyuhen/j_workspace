import prisma from '../../config/database';
import { CreateAbacPolicyInput, UpdateAbacPolicyInput, EvaluateAccessInput } from './abac.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { NotFoundError, ConflictError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

// ======= 条件评估引擎 =======

/** 简易表达式求值器 — 安全沙盒，仅支持基础运算符 */
function evaluateCondition(
  condition: Record<string, any>,
  context: Record<string, any>
): boolean {
  if (!condition) return true;

  // field 操作
  if (condition.field && condition.operator && condition.value !== undefined) {
    const actual = getNestedValue(context, condition.field);
    if (actual === undefined || actual === null) return condition.operator === 'not_exists';

    switch (condition.operator) {
      case 'eq': return actual === condition.value;
      case 'neq': return actual !== condition.value;
      case 'in': return Array.isArray(condition.value) && condition.value.includes(actual);
      case 'not_in': return Array.isArray(condition.value) && !condition.value.includes(actual);
      case 'gt': return Number(actual) > Number(condition.value);
      case 'gte': return Number(actual) >= Number(condition.value);
      case 'lt': return Number(actual) < Number(condition.value);
      case 'lte': return Number(actual) <= Number(condition.value);
      case 'contains': return String(actual).includes(String(condition.value));
      case 'starts_with': return String(actual).startsWith(String(condition.value));
      case 'ends_with': return String(actual).endsWith(String(condition.value));
      case 'exists': return actual !== undefined && actual !== null;
      case 'not_exists': return actual === undefined || actual === null;
      default: return true;
    }
  }

  // AND 逻辑
  if (condition.and && Array.isArray(condition.and)) {
    return condition.and.every((c: any) => evaluateCondition(c, context));
  }

  // OR 逻辑
  if (condition.or && Array.isArray(condition.or)) {
    return condition.or.some((c: any) => evaluateCondition(c, context));
  }

  // NOT 逻辑
  if (condition.not) {
    return !evaluateCondition(condition.not, context);
  }

  return true;
}

/** 从嵌套对象中取值 */
function getNestedValue(obj: Record<string, any>, path: string): any {
  return path.split('.').reduce((acc, key) => acc?.[key], obj as any);
}

/** 检查资源匹配 */
function resourceMatches(
  policyResources: Record<string, any>,
  requestResource: string,
  requestAction: string
): boolean {
  // 如果策略未定义资源限制，视为匹配所有
  if (!policyResources) return true;

  // 检查资源类型匹配
  if (policyResources.type) {
    const types = Array.isArray(policyResources.type) ? policyResources.type : [policyResources.type];
    if (!types.some((t: string) => t === '*' || t === requestResource)) return false;
  }

  // 检查动作匹配
  if (policyResources.actions) {
    const actions = Array.isArray(policyResources.actions) ? policyResources.actions : [policyResources.actions];
    if (!actions.some((a: string) => a === '*' || a === requestAction)) return false;
  }

  return true;
}

// ======= CRUD 操作 =======

async function create(input: CreateAbacPolicyInput) {
  const existing = await prisma.abacPolicy.findUnique({ where: { policyCode: input.policyCode } });
  if (existing) throw new ConflictError(`策略编码 ${input.policyCode} 已存在`);

  const policy = await prisma.abacPolicy.create({
    data: {
      policyCode: input.policyCode,
      policyName: input.policyName,
      resources: input.resources,
      conditions: input.conditions,
      effect: input.effect || 'permit',
      denyOtherwise: input.denyOtherwise ?? false,
      priority: input.priority ?? 0,
      isActive: input.isActive ?? true,
      description: input.description,
    },
  });

  logger.info('ABAC policy created', {
    audit: true,
    eventType: 'ABAC_POLICY_CREATE',
    policyId: policy.id,
    message: `创建ABAC策略 ${policy.policyCode}`,
  });

  return policy;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);

  const where: any = {};
  if (query.keyword) {
    where.OR = [
      { policyCode: { contains: query.keyword, mode: 'insensitive' } },
      { policyName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }
  if (query.effect) where.effect = query.effect;
  if (query.isActive !== undefined) where.isActive = query.isActive === 'true';

  const [policies, total] = await Promise.all([
    prisma.abacPolicy.findMany({
      where,
      ...prismaPagination(pagination),
      orderBy: { priority: 'desc' },
    }),
    prisma.abacPolicy.count({ where }),
  ]);

  return buildPaginatedResult(policies, total, pagination);
}

async function getById(id: string) {
  const policy = await prisma.abacPolicy.findUnique({ where: { id } });
  if (!policy) throw new NotFoundError('AbacPolicy', id);
  return policy;
}

async function update(id: string, input: UpdateAbacPolicyInput) {
  const policy = await prisma.abacPolicy.findUnique({ where: { id } });
  if (!policy) throw new NotFoundError('AbacPolicy', id);

  const updated = await prisma.abacPolicy.update({
    where: { id },
    data: input,
  });

  logger.info('ABAC policy updated', {
    audit: true,
    eventType: 'ABAC_POLICY_UPDATE',
    policyId: id,
  });

  return updated;
}

async function remove(id: string) {
  const policy = await prisma.abacPolicy.findUnique({ where: { id } });
  if (!policy) throw new NotFoundError('AbacPolicy', id);

  await prisma.abacPolicy.delete({ where: { id } });

  logger.info('ABAC policy deleted', {
    audit: true,
    eventType: 'ABAC_POLICY_DELETE',
    policyId: id,
  });

  return { message: '策略已删除' };
}

// ======= 策略评估 =======

/**
 * 评估用户是否有权访问某资源
 * 返回 { allowed: boolean, matchedPolicy?: string, denyReason?: string }
 */
async function evaluateAccess(input: EvaluateAccessInput) {
  // 获取所有活跃策略，按优先级降序
  const policies = await prisma.abacPolicy.findMany({
    where: { isActive: true },
    orderBy: { priority: 'desc' },
  });

  // 构建评估上下文
  const context: Record<string, any> = {
    userId: input.userId,
    resource: input.resource,
    action: input.action,
    ...input.context,
  };

  // 如果能从数据库获取用户信息，添加到上下文
  try {
    const user = await prisma.user.findUnique({
      where: { id: input.userId },
      select: {
        id: true, username: true, displayName: true, department: true,
        organization: true, title: true, status: true,
        userRoles: {
          include: {
            role: { select: { roleCode: true, roleName: true } },
          },
        },
      },
    });
    if (user) {
      context.user = user;
      context.roles = user.userRoles.map(ur => ur.role.roleCode);
      context.departments = user.department ? [user.department] : [];
    }
  } catch {
    // 用户不存在时继续用基本上下文评估
  }

  let denyOtherwiseTriggered = false;

  for (const policy of policies) {
    // 检查资源匹配
    if (!resourceMatches(policy.resources as Record<string, any>, input.resource, input.action)) {
      continue;
    }

    // 评估条件
    const conditionMet = evaluateCondition(
      policy.conditions as Record<string, any>,
      context
    );

    if (!conditionMet) {
      continue;
    }

    // 条件满足，根据策略效果决定
    if (policy.effect === 'deny') {
      return {
        allowed: false,
        matchedPolicy: policy.policyCode,
        matchedPolicyId: policy.id,
        denyReason: `被策略 ${policy.policyName} (${policy.policyCode}) 拒绝`,
      };
    }

    if (policy.effect === 'permit') {
      denyOtherwiseTriggered = policy.denyOtherwise ?? false;
      return {
        allowed: true,
        matchedPolicy: policy.policyCode,
        matchedPolicyId: policy.id,
      };
    }
  }

  // 没有任何策略匹配
  // 如果之前有任何 denyOtherwise=true 的 permit 策略不匹配，则拒绝
  // 默认拒绝（安全原则）
  return {
    allowed: false,
    matchedPolicy: null,
    denyReason: '没有匹配的策略规则，默认拒绝访问',
  };
}

/**
 * 批量评估访问权限
 */
async function batchEvaluate(userId: string, checks: EvaluateAccessInput[]) {
  const results = await Promise.all(
    checks.map(check =>
      evaluateAccess({ ...check, userId, context: check.context })
    )
  );

  return results.map((result, i) => ({
    resource: checks[i].resource,
    action: checks[i].action,
    ...result,
  }));
}

/**
 * 获取适用于某资源的所有策略
 */
async function getEffectivePolicies(resource: string, action?: string) {
  const policies = await prisma.abacPolicy.findMany({
    where: { isActive: true },
    orderBy: { priority: 'desc' },
  });

  return policies.filter(p => {
    const res = p.resources as Record<string, any>;
    if (!res) return true;
    if (res.type) {
      const types = Array.isArray(res.type) ? res.type : [res.type];
      if (!types.some((t: string) => t === '*' || t === resource)) return false;
    }
    if (action && res.actions) {
      const actions = Array.isArray(res.actions) ? res.actions : [res.actions];
      if (!actions.some((a: string) => a === '*' || a === action)) return false;
    }
    return true;
  });
}

export const abacService = {
  create, getList, getById, update, remove,
  evaluateAccess, batchEvaluate, getEffectivePolicies,
};
