import prisma from '../../../config/database';
import { TestRuleInput, ExecuteFormChecksInput } from './edit-check.dto';
import { NotFoundError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

/**
 * 简单表达式求值器
 * 支持：字段比较、数值范围、日期逻辑
 * expression 示例: "AE_ONSET <= today()", "SBP > 180", "WEIGHT > 0 && AGE >= 18"
 */
function evaluateExpression(expression: string, fieldValues: Record<string, any>): boolean {
  try {
    // 将字段引用替换为实际值
    let expr = expression;
    // today() 替换为当前日期字符串
    expr = expr.replace(/today\(\)/g, `"${new Date().toISOString().split('T')[0]}"`);
    // 替换字段引用为值
    for (const [key, value] of Object.entries(fieldValues)) {
      const regex = new RegExp(`\\b${key}\\b`, 'g');
      if (typeof value === 'string') {
        expr = expr.replace(regex, `"${value}"`);
      } else {
        expr = expr.replace(regex, String(value));
      }
    }
    // 将 && 替换为 &&, || 替换为 ||
    expr = expr.replace(/&&/g, ' && ').replace(/\|\|/g, ' || ');
    // 安全求值（仅允许比较操作和逻辑运算）
    if (/^[0-9a-zA-Z"'._:><=!&|() \-]+$/.test(expr)) {
      return new Function(`"use strict"; return (${expr});`)() as boolean;
    }
    return false;
  } catch {
    logger.warn('Edit check expression evaluation failed', { expression, fieldValues });
    return false;
  }
}

/**
 * 根据 EditCheck 规则失败结果自动生成数据质疑
 * 严重程度为 error 时生成自动质疑，warning 级别仅记录日志
 */
async function createAutoQuery(rule: { id: string; ruleName: string; errorMessage: string; severity: string }, input: { projectId: string; subjectId?: string; visitId?: string; formId?: string; fieldValues: Record<string, any> }, userId?: string): Promise<string | null> {
  try {
    // 检查是否已存在相同的自动质疑（避免重复）
    const existingQuery = await prisma.dataQuery.findFirst({
      where: {
        projectId: input.projectId,
        subjectId: input.subjectId,
        formId: input.formId,
        queryType: 'data_discrepancy',
        title: `[EditCheck] ${rule.ruleName}`,
        status: 'open',
      },
    });

    if (existingQuery) {
      // 已存在未关闭的相同质疑，跳过创建
      logger.info('Auto query already exists, skipping', { ruleId: rule.id, queryId: existingQuery.id });
      return existingQuery.id;
    }

    // 创建质疑
    const query = await prisma.dataQuery.create({
      data: {
        projectId: input.projectId,
        subjectId: input.subjectId,
        visitId: input.visitId,
        formId: input.formId,
        queryType: 'data_discrepancy',
        priority: rule.severity === 'error' ? 'high' : 'medium',
        title: `[EditCheck] ${rule.ruleName}`,
        description: rule.errorMessage || `编辑检查规则 "${rule.ruleName}" 校验失败。相关字段值: ${JSON.stringify(input.fieldValues)}`,
        raisedBy: userId || 'system',
        status: 'open',
      },
    });

    // 创建质疑历史记录
    await prisma.dataQueryHistory.create({
      data: {
        queryId: query.id,
        actionType: 'created',
        actionBy: userId || 'system',
        reason: '由编辑检查规则自动生成',
      },
    });

    // 更新执行记录的 queryGenerated 和 queryId
    await prisma.editCheckExecution.updateMany({
      where: {
        ruleId: rule.id,
        projectId: input.projectId,
        subjectId: input.subjectId || undefined,
        formId: input.formId,
        result: 'fail',
        queryGenerated: false,
      },
      data: {
        queryGenerated: true,
        queryId: query.id,
      },
    });

    logger.info('Auto query created from edit check', {
      audit: true,
      eventType: 'DATA_QUERY_CREATE',
      projectId: input.projectId,
      queryId: query.id,
      ruleId: rule.id,
      message: `编辑检查规则 "${rule.ruleName}" 触发自动质疑`,
    });

    return query.id;
  } catch (err) {
    logger.error('Failed to create auto query from edit check', { ruleId: rule.id, error: err });
    return null;
  }
}

/** 测试单条规则 */
async function testRule(input: TestRuleInput) {
  const rule = await prisma.crfEditCheckRule.findUnique({ where: { id: input.ruleId } });
  if (!rule) throw new NotFoundError('CrfEditCheckRule', input.ruleId);
  if (!rule.isActive) {
    return { ruleId: rule.id, ruleName: rule.ruleName, result: 'skipped', reason: '规则已停用' };
  }

  const passed = evaluateExpression(rule.expression, input.fieldValues);

  const execution = await prisma.editCheckExecution.create({
    data: {
      ruleId: rule.id,
      projectId: input.projectId,
      subjectId: input.subjectId || '',
      visitId: input.visitId,
      formId: input.formId || '',
      fieldValues: input.fieldValues,
      result: passed ? 'pass' : 'fail',
      errorMessage: passed ? null : rule.errorMessage,
    },
  });

  return {
    ruleId: rule.id,
    ruleName: rule.ruleName,
    result: passed ? 'pass' : 'fail',
    errorMessage: passed ? null : rule.errorMessage,
    executionId: execution.id,
  };
}

/** 执行表单所有编辑核查规则 */
async function executeFormChecks(input: ExecuteFormChecksInput) {
  const rules = await prisma.crfEditCheckRule.findMany({
    where: { formId: input.formId, isActive: true },
  });

  const results = [];
  for (const rule of rules) {
    const testResult = await testRule({
      ruleId: rule.id,
      fieldValues: input.fieldValues,
      projectId: input.projectId,
      subjectId: input.subjectId,
      visitId: input.visitId,
      formId: input.formId,
    });
    results.push(testResult);

    // 如果规则失败且严重程度为 error，自动生成质疑
    if (testResult.result === 'fail' && rule.severity === 'error') {
      const queryId = await createAutoQuery(rule, input);
      logger.info('Auto query generated from edit check', {
        eventType: 'EDIT_CHECK_AUTO_QUERY',
        ruleId: rule.id,
        subjectId: input.subjectId,
        queryId,
      });
    }
  }

  const passCount = results.filter(r => r.result === 'pass').length;
  const failCount = results.filter(r => r.result === 'fail').length;

  logger.info('Edit checks executed', {
    audit: true,
    eventType: 'EDIT_CHECK_EXECUTE',
    formId: input.formId,
    subjectId: input.subjectId,
    totalRules: rules.length,
    passed: passCount,
    failed: failCount,
  });

  return { total: rules.length, passed: passCount, failed: failCount, results };
}

export const editCheckService = { testRule, executeFormChecks };
