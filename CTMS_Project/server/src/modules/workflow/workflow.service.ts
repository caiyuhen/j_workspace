import prisma from '../../config/database';
import { CreateDefinitionInput, UpdateDefinitionInput, StartInstanceInput, ProcessTaskInput } from './workflow.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { parseSort } from '../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['workflowCode', 'workflowName', 'workflowType', 'status', 'createdAt'];

// ========== 流程定义管理 ==========

async function createDefinition(input: CreateDefinitionInput) {
  const existing = await prisma.workflowDefinition.findUnique({
    where: { workflowCode: input.workflowCode },
  });
  if (existing) throw new ConflictError(`流程编码 ${input.workflowCode} 已存在`);

  const definition = await prisma.workflowDefinition.create({
    data: {
      workflowCode: input.workflowCode,
      workflowName: input.workflowName,
      workflowType: input.workflowType,
      stages: input.stages,
      allowDelegate: input.allowDelegate,
      notificationEnabled: input.notificationEnabled,
    },
  });

  logger.info('Workflow definition created', {
    audit: true,
    eventType: 'WORKFLOW_DEFINITION_CREATE',
    message: `创建流程定义 ${input.workflowCode}`,
  });

  return definition;
}

async function getDefinitionList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'workflowCode', 'asc');

  const where: any = {};
  if (query.workflowType) where.workflowType = query.workflowType;
  if (query.keyword) {
    where.OR = [
      { workflowCode: { contains: query.keyword, mode: 'insensitive' } },
      { workflowName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [definitions, total] = await Promise.all([
    prisma.workflowDefinition.findMany({
      where, ...prismaPagination(pagination),
      orderBy: sort.orderBy,
    }),
    prisma.workflowDefinition.count({ where }),
  ]);

  return buildPaginatedResult(definitions, total, pagination);
}

async function getDefinitionById(id: string) {
  const definition = await prisma.workflowDefinition.findUnique({ where: { id } });
  if (!definition) throw new NotFoundError('WorkflowDefinition', id);
  return definition;
}

async function updateDefinition(id: string, input: UpdateDefinitionInput) {
  const definition = await prisma.workflowDefinition.findUnique({ where: { id } });
  if (!definition) throw new NotFoundError('WorkflowDefinition', id);

  const updated = await prisma.workflowDefinition.update({ where: { id }, data: input });

  logger.info('Workflow definition updated', {
    audit: true,
    eventType: 'WORKFLOW_DEFINITION_UPDATE',
    message: `更新流程定义 ${definition.workflowCode}`,
  });

  return updated;
}

// ========== 流程实例管理 ==========

/**
 * 计算任务的超时截止时间
 * 优先使用 timeoutHours，其次使用 timeoutDays
 */
function calculateDueDate(stage: any): Date | null {
  if (!stage) return null;
  const now = new Date();
  if (stage.timeoutHours && stage.timeoutHours > 0) {
    return new Date(now.getTime() + stage.timeoutHours * 3600 * 1000);
  }
  if (stage.timeoutDays && stage.timeoutDays > 0) {
    return new Date(now.getTime() + stage.timeoutDays * 86400 * 1000);
  }
  return null;
}

/**
 * 获取会签通过所需的最少人数
 */
function getCountersignRequiredCount(stage: any, totalApprovers: number): number {
  if (!stage || !stage.countersignPassMode) return totalApprovers;
  switch (stage.countersignPassMode) {
    case 'one': return 1;
    case 'majority': return Math.ceil(totalApprovers / 2);
    case 'all':
    default: return totalApprovers;
  }
}

async function startInstance(input: StartInstanceInput, userId: string) {
  const definition = await prisma.workflowDefinition.findUnique({
    where: { id: input.definitionId },
  });
  if (!definition) throw new NotFoundError('WorkflowDefinition', input.definitionId);

  const stages = definition.stages as any[];
  const firstStage = stages[0];

  // 创建工作流实例
  const instance = await prisma.workflowInstance.create({
    data: {
      definitionId: input.definitionId,
      workflowType: input.workflowType || definition.workflowType,
      initiatorId: userId,
      projectId: input.projectId,
      businessData: input.businessData || {},
      currentStageIndex: 0,
      status: 'in_progress',
    },
  });

  // 计算超时时间
  const dueAt = calculateDueDate(firstStage);

  // 创建第一个任务
  const taskData: any = {
    instanceId: instance.id,
    stageId: firstStage.id,
    stageName: firstStage.name,
    approverRole: firstStage.approverRole,
    assignedTo: '',
    esigRequired: firstStage.esigRequired || false,
    isCountersign: firstStage.isCountersign || false,
    action: 'pending',
    dueAt,
  };

  // 会签配置
  if (firstStage.isCountersign && firstStage.countersignApprovers && firstStage.countersignApprovers.length > 0) {
    taskData.countersignApprovers = firstStage.countersignApprovers;
    taskData.countersignCompleted = [];
    taskData.assignedTo = firstStage.countersignApprovers.join(',');
  }

  const task = await prisma.workflowTask.create({ data: taskData });

  logger.info('Workflow instance started', {
    audit: true,
    eventType: 'WORKFLOW_START',
    message: `启动流程 ${definition.workflowName}, 实例ID: ${instance.id}`,
  });

  return { instance, currentTask: task };
}

async function getInstanceList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ['status', 'workflowType', 'createdAt'], 'createdAt', 'desc');

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.status) where.status = query.status;
  if (query.workflowType) where.workflowType = query.workflowType;
  if (query.initiatorId) where.initiatorId = query.initiatorId;

  const [instances, total] = await Promise.all([
    prisma.workflowInstance.findMany({
      where, ...prismaPagination(pagination),
      include: {
        definition: { select: { id: true, workflowCode: true, workflowName: true } },
        tasks: { orderBy: { createdAt: 'desc' } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.workflowInstance.count({ where }),
  ]);

  return buildPaginatedResult(instances, total, pagination);
}

async function getInstanceById(id: string) {
  const instance = await prisma.workflowInstance.findUnique({
    where: { id },
    include: {
      definition: true,
      tasks: { orderBy: { createdAt: 'asc' } },
    },
  });

  if (!instance) throw new NotFoundError('WorkflowInstance', id);
  return instance;
}

/**
 * 处理会签：检查是否达到通过条件
 * @returns true = 会签通过，可以流转到下一阶段
 */
async function handleCountersign(task: any, instance: any, stages: any[], userId: string, comment?: string, esigData?: any): Promise<boolean> {
  const stage = stages[instance.currentStageIndex];
  if (!stage) return true;

  const approvers = (task.countersignApprovers as string[]) || [];
  const completed = (task.countersignCompleted as string[]) || [];

  if (!approvers.includes(userId)) {
    throw new BadRequestError('当前用户不在会签审批人列表中');
  }

  if (completed.includes(userId)) {
    throw new BadRequestError('当前用户已完成会签，不可重复操作');
  }

  // 记录会签完成
  const newCompleted = [...completed, userId];
  await prisma.workflowTask.update({
    where: { id: task.id },
    data: {
      countersignCompleted: newCompleted,
      comment: comment || `会签人 ${userId} 已签批`,
      completedAt: new Date(),
    },
  });

  // 检查是否达到通过条件
  const requiredCount = getCountersignRequiredCount(stage, approvers.length);

  if (newCompleted.length >= requiredCount) {
    // 会签通过 → 标记任务完成，流转到下一阶段
    await prisma.workflowTask.update({
      where: { id: task.id },
      data: {
        action: 'approved',
        status: 'completed',
        completedAt: new Date(),
      },
    });

    logger.info('Countersign passed', {
      audit: true,
      eventType: 'WORKFLOW_COUNTERSIGN_PASS',
      message: `会签通过 ${task.id}，已完成 ${newCompleted.length}/${approvers.length}`,
    });

    // 自动流转到下一阶段
    await advanceToNextStage(instance, stages);
    return true;
  }

  logger.info('Countersign progress', {
    audit: true,
    eventType: 'WORKFLOW_COUNTERSIGN_PROGRESS',
    message: `会签进度 ${task.id}，已完成 ${newCompleted.length}/${approvers.length}`,
  });

  return false;
}

/**
 * 流转到下一阶段
 */
async function advanceToNextStage(instance: any, stages: any[]) {
  const nextStageIndex = instance.currentStageIndex + 1;

  if (nextStageIndex < stages.length) {
    const nextStage = stages[nextStageIndex];
    const dueAt = calculateDueDate(nextStage);

    const taskData: any = {
      instanceId: instance.id,
      stageId: nextStage.id,
      stageName: nextStage.name,
      approverRole: nextStage.approverRole,
      assignedTo: '',
      esigRequired: nextStage.esigRequired || false,
      isCountersign: nextStage.isCountersign || false,
      action: 'pending',
      dueAt,
    };

    // 会签配置
    if (nextStage.isCountersign && nextStage.countersignApprovers && nextStage.countersignApprovers.length > 0) {
      taskData.countersignApprovers = nextStage.countersignApprovers;
      taskData.countersignCompleted = [];
      taskData.assignedTo = nextStage.countersignApprovers.join(',');
    }

    await prisma.workflowTask.create({ data: taskData });
    await prisma.workflowInstance.update({
      where: { id: instance.id },
      data: { currentStageIndex: nextStageIndex },
    });
  } else {
    // 所有阶段通过 → 流程完成
    await prisma.workflowInstance.update({
      where: { id: instance.id },
      data: { status: 'approved', result: 'approved', completedAt: new Date() },
    });
  }
}

/**
 * 处理退回到指定阶段
 */
async function handleReturn(task: any, instance: any, stages: any[], returnToStageId: string, userId: string, comment?: string) {
  const currentStage = stages[instance.currentStageIndex];
  if (!currentStage) throw new BadRequestError('当前阶段信息异常');

  // 检查退回权限
  if (currentStage.allowReturn === false) {
    throw new BadRequestError('当前节点不允许退回操作');
  }

  // 验证目标阶段
  let targetStageIndex = -1;
  if (returnToStageId) {
    targetStageIndex = stages.findIndex((s: any) => s.id === returnToStageId);
    if (targetStageIndex === -1) {
      throw new BadRequestError(`目标退回阶段 ${returnToStageId} 不存在`);
    }
    if (targetStageIndex >= instance.currentStageIndex) {
      throw new BadRequestError('只能退回到之前的阶段');
    }
    // 如果配置了允许退回的阶段列表，检查是否在列表中
    if (currentStage.returnToStageIds && (currentStage.returnToStageIds as string[]).length > 0) {
      if (!(currentStage.returnToStageIds as string[]).includes(returnToStageId)) {
        throw new BadRequestError('当前节点不允许退回到指定阶段');
      }
    }
  } else {
    // 默认退回到上一阶段
    targetStageIndex = instance.currentStageIndex - 1;
    if (targetStageIndex < 0) {
      throw new BadRequestError('已经是第一个阶段，无法退回');
    }
  }

  const targetStage = stages[targetStageIndex];
  const dueAt = calculateDueDate(targetStage);

  // 标记当前任务为已退回
  await prisma.workflowTask.update({
    where: { id: task.id },
    data: {
      action: 'returned',
      status: 'returned',
      comment: comment || `退回到 ${targetStage.name}`,
      completedAt: new Date(),
    },
  });

  // 在目标阶段创建新任务
  const newTaskData: any = {
    instanceId: instance.id,
    stageId: targetStage.id,
    stageName: targetStage.name,
    approverRole: targetStage.approverRole,
    assignedTo: '',
    esigRequired: targetStage.esigRequired || false,
    isCountersign: targetStage.isCountersign || false,
    action: 'pending',
    dueAt,
  };

  if (targetStage.isCountersign && targetStage.countersignApprovers && targetStage.countersignApprovers.length > 0) {
    newTaskData.countersignApprovers = targetStage.countersignApprovers;
    newTaskData.countersignCompleted = [];
    newTaskData.assignedTo = targetStage.countersignApprovers.join(',');
  }

  await prisma.workflowTask.create({ data: newTaskData });

  // 更新实例当前阶段
  await prisma.workflowInstance.update({
    where: { id: instance.id },
    data: { currentStageIndex: targetStageIndex },
  });

  logger.info('Workflow task returned', {
    audit: true,
    eventType: 'WORKFLOW_TASK_RETURN',
    message: `任务 ${task.id} 退回到 ${targetStage.name}（阶段${targetStageIndex}）`,
  });
}

async function processTask(taskId: string, input: ProcessTaskInput, userId: string) {
  const task = await prisma.workflowTask.findUnique({
    where: { id: taskId },
  });
  if (!task) throw new NotFoundError('WorkflowTask', taskId);
  if (task.status === 'completed' || task.status === 'returned') {
    throw new BadRequestError('该任务已处理完成');
  }

  const instance = await prisma.workflowInstance.findUnique({
    where: { id: task.instanceId },
    include: { definition: true },
  });
  if (!instance) throw new NotFoundError('WorkflowInstance', task.instanceId);
  if (instance.status !== 'in_progress') {
    throw new BadRequestError('流程已结束，无法操作');
  }

  const stages = instance.definition.stages as any[];

  // 会签处理
  if (input.action === 'countersign') {
    if (!task.isCountersign) {
      throw new BadRequestError('当前任务不是会签类型');
    }
    await handleCountersign(task, instance, stages, userId, input.comment, input.esigData);
    return getInstanceById(instance.id);
  }

  // 电子签名校验
  if (task.esigRequired && input.action !== 'delegate' && input.action !== 'return') {
    if (!input.esigData) {
      throw new BadRequestError('该审批节点需要电子签名');
    }
  }

  // 构建任务更新数据
  const updateData: any = {
    action: input.action,
    status: 'completed',
    comment: input.comment,
    completedAt: new Date(),
  };

  if (input.esigData) {
    updateData.esigData = {
      ...input.esigData,
      signedBy: userId,
      signedAt: new Date().toISOString(),
    };
  }

  // 双签名支持（核准节点等）
  if (input.esigDataSecondary) {
    const currentEsig = (task.esigData as any) || {};
    updateData.esigData = {
      ...updateData.esigData,
      dualSign: true,
      signatures: [
        ...(currentEsig.signatures || []),
        {
          ...input.esigDataSecondary,
          signedBy: userId,
          signedAt: new Date().toISOString(),
        },
      ],
    };
  }

  await prisma.workflowTask.update({
    where: { id: taskId },
    data: updateData,
  });

  // 处理不同操作类型
  if (input.action === 'delegate') {
    if (instance.definition.allowDelegate === false) {
      throw new BadRequestError('该流程不允许委托操作');
    }
    if (!input.delegateTo) throw new BadRequestError('委托操作需要指定 delegateTo');
    await prisma.workflowTask.create({
      data: {
        instanceId: instance.id,
        stageId: task.stageId,
        stageName: task.stageName,
        approverRole: task.approverRole,
        assignedTo: input.delegateTo,
        esigRequired: task.esigRequired,
        isCountersign: task.isCountersign,
        countersignApprovers: task.countersignApprovers || undefined,
        countersignCompleted: task.countersignCompleted || undefined,
        action: null,
      },
    });
  } else if (input.action === 'return') {
    // 退回到指定阶段
    await handleReturn(task, instance, stages, input.returnToStageId || '', userId, input.comment);
  } else if (input.action === 'reject') {
    // 驳回 → 整个流程结束
    await prisma.workflowInstance.update({
      where: { id: instance.id },
      data: { status: 'rejected', result: 'rejected', completedAt: new Date() },
    });
  } else if (input.action === 'approve') {
    // 流转到下一阶段
    await advanceToNextStage(instance, stages);
  }

  const actionLabels: Record<string, string> = {
    approve: '批准', reject: '驳回', delegate: '委托', return: '退回', countersign: '会签',
  };

  logger.info(`Workflow task ${input.action}`, {
    audit: true,
    eventType: `WORKFLOW_TASK_${input.action.toUpperCase()}`,
    message: `任务 ${taskId} 已${actionLabels[input.action] || input.action}`,
  });

  return getInstanceById(instance.id);
}

// ========== 待办任务查询 ==========

async function getMyPendingTasks(userId: string, query: Record<string, any>) {
  const pagination = parsePagination(query);

  const where: any = {
    status: 'pending',
  };

  // 普通任务：精确匹配 assignedTo
  // 会签任务：assignedTo 包含 userId（逗号分隔列表）
  where.OR = [
    { assignedTo: userId },
    { assignedTo: { contains: userId } },
  ];

  const [tasks, total] = await Promise.all([
    prisma.workflowTask.findMany({
      where, ...prismaPagination(pagination),
      include: {
        instance: {
          include: {
            definition: { select: { workflowCode: true, workflowName: true } },
          },
        },
      },
      orderBy: { createdAt: 'asc' },
    }),
    prisma.workflowTask.count({ where }),
  ]);

  return buildPaginatedResult(tasks, total, pagination);
}

// ========== 超时任务管理 ==========

/**
 * 获取已超时或即将超时的任务
 */
async function getTimeoutTasks(query: Record<string, any>) {
  const now = new Date();
  const overdueOnly = query.overdueOnly !== 'false';

  const where: any = {
    status: 'pending',
    dueAt: overdueOnly ? { lte: now } : { lte: new Date(now.getTime() + 24 * 3600 * 1000) },
  };

  const [tasks, total] = await Promise.all([
    prisma.workflowTask.findMany({
      where,
      include: {
        instance: {
          include: {
            definition: { select: { workflowCode: true, workflowName: true } },
          },
        },
      },
      orderBy: { dueAt: 'asc' },
    }),
    prisma.workflowTask.count({ where }),
  ]);

  return {
    tasks,
    total,
    checkedAt: now.toISOString(),
    overdueOnly,
  };
}

/**
 * 自动处理超时任务（可由定时任务调用）
 * 超时策略：
 * - 1. 自动通知相关人员
 * - 2. 根据配置自动退回或升级
 */
async function processTimeoutTasks() {
  const now = new Date();
  const timeoutTasks = await prisma.workflowTask.findMany({
    where: {
      status: 'pending',
      dueAt: { lte: now },
    },
    include: {
      instance: {
        include: { definition: true },
      },
    },
  });

  const results: any[] = [];

  for (const task of timeoutTasks) {
    const stages = task.instance.definition.stages as any[];
    const currentStage = stages[task.instance.currentStageIndex];

    // 记录超时事件
    logger.warn('Workflow task timeout', {
      audit: true,
      eventType: 'WORKFLOW_TASK_TIMEOUT',
      message: `任务 ${task.id}（${task.stageName}）已超时`,
      extra: {
        taskId: task.id,
        instanceId: task.instance.id,
        stageName: task.stageName,
        dueAt: task.dueAt,
        timeoutStrategy: currentStage?.timeoutStrategy || 'notify',
      },
    });

    const timeoutStrategy = currentStage?.timeoutStrategy || 'notify';

    if (timeoutStrategy === 'auto_return') {
      // 自动退回到上一阶段或发起人
      try {
        await handleReturn(task, task.instance, stages, '', 'system', '系统自动退回：审批超时');
        results.push({ taskId: task.id, action: 'auto_returned', status: 'success' });
      } catch (err: any) {
        results.push({ taskId: task.id, action: 'auto_return_failed', status: 'error', message: err.message });
      }
    } else if (timeoutStrategy === 'auto_approve') {
      // 超时自动通过（仅适用于备案等非关键节点）
      await prisma.workflowTask.update({
        where: { id: task.id },
        data: {
          action: 'auto_approved',
          status: 'completed',
          comment: '系统自动批准：审批超时',
          completedAt: now,
        },
      });
      await advanceToNextStage(task.instance, stages);
      results.push({ taskId: task.id, action: 'auto_approved', status: 'success' });
    } else {
      // 默认策略：仅通知（通知逻辑由 notification 模块处理）
      results.push({ taskId: task.id, action: 'notified', status: 'success' });
    }
  }

  return {
    processedAt: now.toISOString(),
    totalTimeoutTasks: timeoutTasks.length,
    results,
  };
}

/**
 * 撤销流程实例（仅发起人或管理员可操作）
 */
async function cancelInstance(instanceId: string, userId: string, reason: string) {
  const instance = await prisma.workflowInstance.findUnique({
    where: { id: instanceId },
  });
  if (!instance) throw new NotFoundError('WorkflowInstance', instanceId);
  if (instance.initiatorId !== userId) {
    throw new BadRequestError('仅发起人可以撤销流程');
  }
  if (instance.status !== 'in_progress') {
    throw new BadRequestError('只能撤销进行中的流程');
  }

  // 取消所有待处理任务
  await prisma.workflowTask.updateMany({
    where: {
      instanceId,
      status: 'pending',
    },
    data: {
      status: 'cancelled',
      action: 'cancelled',
      comment: `流程已撤销：${reason}`,
      completedAt: new Date(),
    },
  });

  // 更新实例状态
  const updated = await prisma.workflowInstance.update({
    where: { id: instanceId },
    data: { status: 'cancelled', result: 'cancelled', completedAt: new Date() },
  });

  logger.info('Workflow instance cancelled', {
    audit: true,
    eventType: 'WORKFLOW_CANCEL',
    message: `流程 ${instanceId} 已撤销`,
  });

  return updated;
}

// ========== 流程统计 ==========

async function getWorkflowStats(query: Record<string, any>) {
  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.workflowType) where.workflowType = query.workflowType;

  const [totalCount, statusCounts, pendingTaskCount, timeoutTaskCount] = await Promise.all([
    prisma.workflowInstance.count({ where }),
    prisma.workflowInstance.groupBy({
      by: ['status'],
      where,
      _count: { status: true },
    }),
    prisma.workflowTask.count({
      where: { status: 'pending' },
    }),
    prisma.workflowTask.count({
      where: {
        status: 'pending',
        dueAt: { lte: new Date() },
      },
    }),
  ]);

  const statusMap: Record<string, number> = {};
  for (const item of statusCounts) {
    statusMap[item.status] = item._count.status;
  }

  return {
    total: totalCount,
    byStatus: statusMap,
    pendingTasks: pendingTaskCount,
    timeoutTasks: timeoutTaskCount,
  };
}

export const workflowService = {
  createDefinition, getDefinitionList, getDefinitionById, updateDefinition,
  startInstance, getInstanceList, getInstanceById, processTask, getMyPendingTasks,
  getTimeoutTasks, processTimeoutTasks, cancelInstance, getWorkflowStats,
};
