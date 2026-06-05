import prisma from '../../config/database';
import { ChatInput, BatchProcessInput, AnalyzeInput } from './ai.dto';
import { NotFoundError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';

const LLM_API_URL = 'http://192.168.0.126:8802/write/';

/**
 * 调用内网大模型
 */
async function callLLM(systemPrompt: string, userMessage: string): Promise<any> {
  const startTime = Date.now();

  try {
    const response = await fetch(LLM_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'default',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userMessage },
        ],
        temperature: 0.3,
        max_tokens: 4096,
      }),
    });

    if (!response.ok) {
      throw new Error(`LLM API 返回错误: ${response.status} ${response.statusText}`);
    }

    const result: any = await response.json();
    const durationMs = Date.now() - startTime;

    return {
      content: result.choices?.[0]?.message?.content || result.response || result.content || '',
      modelUsed: result.model || 'default',
      tokensUsed: result.usage?.total_tokens || 0,
      durationMs,
    };
  } catch (error: any) {
    const durationMs = Date.now() - startTime;
    throw new Error(`LLM 调用失败 (${durationMs}ms): ${error.message}`);
  }
}

/**
 * 获取 Agent 系统提示
 */
function getAgentSystemPrompt(agentType: string): string {
  const prompts: Record<string, string> = {
    doc_review: '你是一个临床试验文档审查专家。请审查提供的文档内容，检查其合规性、完整性和准确性，参照ICH GCP E6(R2)标准。用中文回答。',
    ae_coding: '你是一个不良事件编码专家，精通 MedDRA 词典。请根据提供的不良事件描述，给出推荐的 MedDRA 编码（LLT/PT/SOC），用中文回答。',
    cons_audit: '你是一个知情同意书审核专家。请检查知情同意书是否包含所有必需要素（ICH GCP E6(R2) 4.8.10），用中文回答。',
    sdv_assist: '你是一个源数据核查（SDV）辅助专家。请根据提供的CRF数据和源文档信息，辅助核查数据一致性，标记潜在差异，用中文回答。',
    sae_alert: '你是一个SAE（严重不良事件）预警分析专家。请分析提供的SAE数据，识别潜在安全信号，评估风险等级，用中文回答。',
    prot_check: '你是一个临床试验方案依从性检查专家。请检查受试者数据是否符合方案要求，识别方案偏离，用中文回答。',
    lab_norm: '你是一个实验室数据正常值范围检查专家。请分析提供的实验室检查数据，标记异常值，用中文回答。',
    data_clean: '你是一个临床数据清洗专家。请检查提供的数据记录，识别数据质量问题（缺失值、逻辑错误、异常值等），用中文回答。',
    qm_report: '你是一个临床试验质量管理报告专家。请根据提供的项目数据，生成质量管理分析报告，用中文回答。',
    work_hour: '你是一个工时分析专家。请分析提供的工时数据，识别工时分配异常、效率问题和优化建议，用中文回答。',
    chatbot: '你是一个临床试验管理系统（CTMS/EDC）的智能助手。请回答用户关于临床试验管理、数据录入、合规要求等方面的问题，用中文回答。',
    translate: '你是一个医学文献翻译专家，精通中英双语。请将提供的医学文献准确翻译，保持专业术语的准确性，用中文回答。',
  };

  return prompts[agentType] || prompts.chatbot;
}

/**
 * 获取 Agent 描述
 */
function getAgentDescription(agentType: string): string {
  const descriptions: Record<string, string> = {
    doc_review: '文档合规审查',
    ae_coding: 'AE MedDRA编码',
    cons_audit: '知情同意书审核',
    sdv_assist: 'SDV源数据核查辅助',
    sae_alert: 'SAE安全信号预警',
    prot_check: '方案依从性检查',
    lab_norm: '实验室异常值检查',
    data_clean: '数据质量清洗',
    qm_report: '质量管理报告生成',
    work_hour: '工时分析优化',
    chatbot: '智能问答助手',
    translate: '医学文献翻译',
  };
  return descriptions[agentType] || '未知';
}

/**
 * AI 对话
 */
async function chat(input: ChatInput, userId: string) {
  const systemPrompt = getAgentSystemPrompt(input.agentType);

  // 构建上下文消息
  let userMessage = input.message;
  if (input.contextData && Object.keys(input.contextData).length > 0) {
    userMessage = `[项目上下文数据]\n${JSON.stringify(input.contextData, null, 2)}\n\n[用户问题]\n${input.message}`;
  }

  const startTime = Date.now();
  let llmResult: any;
  let status = 'success';
  let errorMessage: string | undefined;

  try {
    llmResult = await callLLM(systemPrompt, userMessage);
  } catch (error: any) {
    status = 'error';
    errorMessage = error.message;
    llmResult = { content: `AI 处理失败: ${error.message}`, modelUsed: 'unknown', tokensUsed: 0, durationMs: Date.now() - startTime };
  }

  // 记录 Agent 日志
  await prisma.aiAgentLog.create({
    data: {
      agentType: input.agentType,
      projectId: input.projectId,
      userId,
      input: { message: input.message, contextData: input.contextData },
      output: { content: llmResult.content },
      modelUsed: llmResult.modelUsed,
      tokensUsed: llmResult.tokensUsed,
      durationMs: llmResult.durationMs,
      status,
      errorMessage,
    },
  });

  logger.info('AI agent chat', {
    audit: true,
    eventType: 'AI_CHAT',
    agentType: input.agentType,
    message: `${input.agentType} 对话, 耗时 ${llmResult.durationMs}ms`,
  });

  return {
    agentType: input.agentType,
    description: getAgentDescription(input.agentType),
    content: llmResult.content,
    modelUsed: llmResult.modelUsed,
    tokensUsed: llmResult.tokensUsed,
    durationMs: llmResult.durationMs,
    status,
  };
}

/**
 * 批量处理
 */
async function batchProcess(input: BatchProcessInput, userId: string) {
  const systemPrompt = getAgentSystemPrompt(input.agentType);
  const results: any[] = [];

  for (let i = 0; i < input.items.length; i++) {
    const item = input.items[i];
    const userMessage = `[项目ID: ${input.projectId}]\n[数据项 ${i + 1}/${input.items.length}]\n${JSON.stringify(item, null, 2)}\n\n请分析此数据项。`;

    const startTime = Date.now();
    let llmResult: any;
    let status = 'success';
    let errorMessage: string | undefined;

    try {
      llmResult = await callLLM(systemPrompt, userMessage);
    } catch (error: any) {
      status = 'error';
      errorMessage = error.message;
      llmResult = { content: `处理失败: ${error.message}`, modelUsed: 'unknown', tokensUsed: 0, durationMs: Date.now() - startTime };
    }

    await prisma.aiAgentLog.create({
      data: {
        agentType: input.agentType,
        projectId: input.projectId,
        userId,
        input: { item, options: input.options },
        output: { content: llmResult.content },
        modelUsed: llmResult.modelUsed,
        tokensUsed: llmResult.tokensUsed,
        durationMs: llmResult.durationMs,
        status,
        errorMessage,
      },
    });

    results.push({
      index: i,
      content: llmResult.content,
      status,
      durationMs: llmResult.durationMs,
    });
  }

  return {
    agentType: input.agentType,
    totalItems: input.items.length,
    successCount: results.filter(r => r.status === 'success').length,
    errorCount: results.filter(r => r.status !== 'success').length,
    results,
  };
}

/**
 * 数据分析
 */
async function analyze(input: AnalyzeInput, userId: string) {
  const systemPrompt = getAgentSystemPrompt(input.agentType);
  const userMessage = `[分析类型: ${input.analysisType}]\n[项目ID: ${input.projectId}]\n[参数: ${JSON.stringify(input.parameters || {})}]\n\n请执行分析并给出详细报告。`;

  const startTime = Date.now();
  let llmResult: any;
  let status = 'success';
  let errorMessage: string | undefined;

  try {
    llmResult = await callLLM(systemPrompt, userMessage);
  } catch (error: any) {
    status = 'error';
    errorMessage = error.message;
    llmResult = { content: `分析失败: ${error.message}`, modelUsed: 'unknown', tokensUsed: 0, durationMs: Date.now() - startTime };
  }

  await prisma.aiAgentLog.create({
    data: {
      agentType: input.agentType,
      projectId: input.projectId,
      userId,
      input: { analysisType: input.analysisType, parameters: input.parameters },
      output: { content: llmResult.content },
      modelUsed: llmResult.modelUsed,
      tokensUsed: llmResult.tokensUsed,
      durationMs: llmResult.durationMs,
      status,
      errorMessage,
    },
  });

  logger.info('AI agent analyze', {
    audit: true,
    eventType: 'AI_ANALYZE',
    agentType: input.agentType,
    message: `${input.agentType} 分析: ${input.analysisType}`,
  });

  return {
    agentType: input.agentType,
    description: getAgentDescription(input.agentType),
    analysisType: input.analysisType,
    content: llmResult.content,
    modelUsed: llmResult.modelUsed,
    tokensUsed: llmResult.tokensUsed,
    durationMs: llmResult.durationMs,
    status,
  };
}

/**
 * 获取 Agent 列表
 */
function getAgentList() {
  const agentTypes = [
    'doc_review', 'ae_coding', 'cons_audit', 'sdv_assist', 'sae_alert',
    'prot_check', 'lab_norm', 'data_clean', 'qm_report', 'work_hour',
    'chatbot', 'translate',
  ] as const;

  return agentTypes.map(type => ({
    agentType: type,
    name: getAgentDescription(type),
    description: getAgentSystemPrompt(type).substring(0, 100) + '...',
  }));
}

/**
 * 获取 Agent 调用日志
 */
async function getLogs(query: Record<string, any>) {
  const where: any = {};
  if (query.agentType) where.agentType = query.agentType;
  if (query.projectId) where.projectId = query.projectId;
  if (query.userId) where.userId = query.userId;
  if (query.status) where.status = query.status;

  const pagination = parsePagination(query);

  const [logs, total] = await Promise.all([
    prisma.aiAgentLog.findMany({
      where, ...prismaPagination(pagination),
      orderBy: { createdAt: 'desc' },
    }),
    prisma.aiAgentLog.count({ where }),
  ]);

  return buildPaginatedResult(logs, total, pagination);
}

export const aiService = {
  chat, batchProcess, analyze, getAgentList, getLogs,
};
