import prisma from '../../../config/database';
import { CreateTemplateInput, UpdateTemplateInput, CloneTemplateInput } from './template.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['templateCode', 'templateName', 'templateType', 'version', 'status', 'createdAt'];

/**
 * 创建模板
 */
async function create(input: CreateTemplateInput) {
  const existing = await prisma.edcTemplate.findFirst({
    where: { templateCode: input.templateCode, version: input.version },
  });
  if (existing) throw new ConflictError(`模板编码 ${input.templateCode} 版本 ${input.version} 已存在`);

  const template = await prisma.edcTemplate.create({
    data: {
      ...input,
      status: 'draft',
    },
  });

  logger.info('EDC template created', {
    audit: true,
    eventType: 'TEMPLATE_CREATE',
    message: `创建模板 ${input.templateCode} v${input.version}`,
  });

  return template;
}

/**
 * 获取模板列表
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.keyword) {
    where.OR = [
      { templateCode: { contains: query.keyword, mode: 'insensitive' } },
      { templateName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }
  if (query.templateType) where.templateType = query.templateType;
  if (query.status) where.status = query.status;
  if (query.projectId) where.projectId = query.projectId;
  if (query.isSystemTemplate !== undefined) where.isSystemTemplate = query.isSystemTemplate === 'true';
  if (query.isShared !== undefined) where.isShared = query.isShared === 'true';

  const [templates, total] = await Promise.all([
    prisma.edcTemplate.findMany({
      where, ...prismaPagination(pagination),
      include: {
        project: { select: { id: true, projectCode: true, projectName: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.edcTemplate.count({ where }),
  ]);

  return buildPaginatedResult(templates, total, pagination);
}

/**
 * 获取模板详情（含完整 templateData）
 */
async function getById(id: string) {
  const template = await prisma.edcTemplate.findUnique({
    where: { id },
    include: {
      project: { select: { id: true, projectCode: true, projectName: true } },
    },
  });
  if (!template) throw new NotFoundError('EdcTemplate', id);
  return template;
}

/**
 * 更新模板
 */
async function update(id: string, input: UpdateTemplateInput) {
  const template = await prisma.edcTemplate.findUnique({ where: { id } });
  if (!template) throw new NotFoundError('EdcTemplate', id);
  if (template.status === 'published' && input.status !== 'deprecated') {
    throw new BadRequestError('已发布的模板只能变更为废弃状态，不能修改内容');
  }

  const updated = await prisma.edcTemplate.update({ where: { id }, data: input });

  logger.info('EDC template updated', {
    audit: true,
    eventType: 'TEMPLATE_UPDATE',
    message: `更新模板 ${template.templateCode}`,
  });

  return updated;
}

/**
 * 发布模板
 */
async function publish(id: string) {
  const template = await prisma.edcTemplate.findUnique({ where: { id } });
  if (!template) throw new NotFoundError('EdcTemplate', id);
  if (template.status !== 'draft') throw new BadRequestError('只有草稿状态的模板可以发布');

  const updated = await prisma.edcTemplate.update({
    where: { id },
    data: { status: 'published' },
  });

  logger.info('EDC template published', {
    audit: true,
    eventType: 'TEMPLATE_PUBLISH',
    message: `发布模板 ${template.templateCode} v${template.version}`,
  });

  return updated;
}

/**
 * 废弃模板
 */
async function deprecate(id: string) {
  const template = await prisma.edcTemplate.findUnique({ where: { id } });
  if (!template) throw new NotFoundError('EdcTemplate', id);

  const updated = await prisma.edcTemplate.update({
    where: { id },
    data: { status: 'deprecated' },
  });

  logger.info('EDC template deprecated', {
    audit: true,
    eventType: 'TEMPLATE_DEPRECATE',
    message: `废弃模板 ${template.templateCode}`,
  });

  return updated;
}

/**
 * 克隆模板
 */
async function clone(id: string, input: CloneTemplateInput) {
  const source = await prisma.edcTemplate.findUnique({ where: { id } });
  if (!source) throw new NotFoundError('EdcTemplate', id);

  const newVersion = input.newVersion || source.version;
  const existing = await prisma.edcTemplate.findFirst({
    where: { templateCode: input.newTemplateCode, version: newVersion },
  });
  if (existing) throw new ConflictError(`模板编码 ${input.newTemplateCode} 版本 ${newVersion} 已存在`);

  const cloned = await prisma.edcTemplate.create({
    data: {
      templateCode: input.newTemplateCode,
      templateName: input.newTemplateName,
      templateType: source.templateType,
      version: newVersion,
      templateData: JSON.parse(JSON.stringify(source.templateData)),
      description: source.description,
      projectId: input.projectId || source.projectId,
      isSystemTemplate: false,
      isShared: false,
      status: 'draft',
    },
  });

  logger.info('EDC template cloned', {
    audit: true,
    eventType: 'TEMPLATE_CLONE',
    message: `从 ${source.templateCode} 克隆为 ${input.newTemplateCode}`,
  });

  return cloned;
}

export const templateService = {
  create, getList, getById, update, publish, deprecate, clone,
};
