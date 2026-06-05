import prisma from '../../../config/database';
import { CreateFormInput, UpdateFormInput, AddFieldInputFinal, CreateEditCheckRuleInput, PublishFormInput } from './form.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['formName', 'formType', 'status', 'version', 'createdAt', 'updatedAt'];

async function validateCodeListOid(codeListOid?: string) {
  if (!codeListOid) return null;

  const codeList = await prisma.cdiscCodeList.findUnique({
    where: { codeListOid },
    select: { codeListOid: true, domain: true, dataType: true },
  });

  if (!codeList) {
    throw new BadRequestError(`CDISC 代码表不存在: ${codeListOid}`);
  }

  return codeList;
}

/**
 * 创建CRF表单
 */
async function create(input: CreateFormInput, userId: string) {
  const { fields, ...formData } = input;

  // 检查项目是否存在
  const project = await prisma.project.findUnique({ where: { id: input.projectId } });
  if (!project) throw new NotFoundError('Project', input.projectId);

  // 检查表单编码是否已存在
  const existing = await prisma.crfForm.findUnique({
    where: { projectId_formCode: { projectId: input.projectId, formCode: input.formCode } },
  });
  if (existing) throw new ConflictError('表单编码已存在');

  const form = await prisma.crfForm.create({
    data: {
      ...formData,
      createdBy: userId,
      fields: fields ? {
        create: await Promise.all(fields.map(async (f) => {
          const codeList = await validateCodeListOid(f.codeListOid);

          return {
            ...f,
            cdiscDomain: f.cdiscDomain || input.cdiscDomain,
            cdashDataset: f.cdashDataset || input.cdiscDomain || input.formCode,
            cdashDataType: f.cdashDataType || f.fieldType,
            options: f.options || [],
            codeListOid: f.codeListOid,
            standardMetadata: {
              ...(f.standardMetadata || {}),
              codeListDataType: codeList?.dataType || null,
            },
          };
        })),
      } : undefined,
    },
    include: { fields: { orderBy: { sortOrder: 'asc' } } },
  });

  logger.info('CRF form created', {
    audit: true,
    eventType: 'CRF_FORM_CREATE',
    projectId: input.projectId,
    message: `创建CRF表单: ${input.formName}`,
  });

  return form;
}

/**
 * 获取表单列表
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.status) where.status = query.status;
  if (query.formType) where.formType = query.formType;
  if (query.cdiscDomain) where.cdiscDomain = query.cdiscDomain;
  if (query.keyword) {
    where.OR = [
      { formName: { contains: query.keyword, mode: 'insensitive' } },
      { formCode: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [forms, total] = await Promise.all([
    prisma.crfForm.findMany({
      where, ...prismaPagination(pagination),
      include: {
        fields: {
          orderBy: { sortOrder: 'asc' },
          select: {
            id: true,
            fieldCode: true,
            fieldName: true,
            fieldType: true,
            controlType: true,
            cdiscDomain: true,
            cdashVariable: true,
            sdtmVariable: true,
          },
        },
        _count: { select: { fields: true, editCheckRules: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.crfForm.count({ where }),
  ]);

  return buildPaginatedResult(forms, total, pagination);
}

/**
 * 获取表单详情
 */
async function getById(id: string) {
  const form = await prisma.crfForm.findUnique({
    where: { id },
    include: {
      fields: { orderBy: { sortOrder: 'asc' } },
      editCheckRules: { where: { isActive: true } },
    },
  });

  if (!form) throw new NotFoundError('CrfForm', id);

  // 获取最新版本号
  const latestVersion = await prisma.crfFormVersion.findFirst({
    where: { formId: id },
    orderBy: { createdAt: 'desc' },
    select: { version: true },
  });

  return { ...form, latestVersion: latestVersion?.version || form.version };
}

/**
 * 更新表单
 */
async function update(id: string, input: UpdateFormInput, userId: string) {
  const form = await prisma.crfForm.findUnique({ where: { id } });
  if (!form) throw new NotFoundError('CrfForm', id);
  if (form.status === 'published') throw new BadRequestError('已发布的表单不能直接修改，请新建版本');

  const updated = await prisma.crfForm.update({
    where: { id },
    data: input,
  });

  logger.info('CRF form updated', {
    audit: true,
    eventType: 'CRF_FORM_UPDATE',
    projectId: form.projectId,
    message: `更新CRF表单: ${form.formName}`,
  });

  return updated;
}

/**
 * 删除表单
 */
async function remove(id: string) {
  const form = await prisma.crfForm.findUnique({ where: { id } });
  if (!form) throw new NotFoundError('CrfForm', id);
  if (form.status === 'published') throw new BadRequestError('已发布的表单不能删除');

  await prisma.crfForm.delete({ where: { id } });

  logger.info('CRF form deleted', {
    audit: true,
    eventType: 'CRF_FORM_DELETE',
    projectId: form.projectId,
    message: `删除CRF表单: ${form.formName}`,
  });

  return { success: true };
}

/**
 * 添加字段
 */
async function addField(formId: string, input: AddFieldInputFinal, userId: string) {
  const form = await prisma.crfForm.findUnique({ where: { id: formId } });
  if (!form) throw new NotFoundError('CrfForm', formId);
  const codeList = await validateCodeListOid(input.codeListOid);

  // 检查字段编码是否已存在
  const existing = await prisma.crfFormField.findUnique({
    where: { formId_fieldCode: { formId, fieldCode: input.fieldCode } },
  });
  if (existing) throw new ConflictError('字段编码已存在');

  const field = await prisma.crfFormField.create({
    data: {
      formId,
      ...input,
      cdiscDomain: input.cdiscDomain || form.cdiscDomain,
      cdashDataset: input.cdashDataset || form.cdiscDomain || form.formCode,
      cdashDataType: input.cdashDataType || input.fieldType,
      standardMetadata: {
        ...(input.standardMetadata || {}),
        codeListDataType: codeList?.dataType || null,
      },
      options: input.options || [],
    },
  });

  logger.info('CRF field added', {
    audit: true,
    eventType: 'CRF_FIELD_ADD',
    projectId: form.projectId,
    message: `添加字段: ${input.fieldName} 到表单 ${form.formName}`,
  });

  return field;
}

/**
 * 更新字段
 */
async function updateField(formId: string, fieldId: string, input: Partial<AddFieldInputFinal>) {
  const field = await prisma.crfFormField.findFirst({ where: { id: fieldId, formId } });
  if (!field) throw new NotFoundError('CrfFormField', fieldId);
  const form = await prisma.crfForm.findUnique({ where: { id: formId } });
  const codeList = await validateCodeListOid(input.codeListOid);

  return prisma.crfFormField.update({
    where: { id: fieldId },
    data: {
      ...input,
      cdiscDomain: input.cdiscDomain || field.cdiscDomain || form?.cdiscDomain,
      cdashDataset: input.cdashDataset || field.cdashDataset || form?.cdiscDomain || form?.formCode,
      cdashDataType: input.cdashDataType || field.cdashDataType,
      standardMetadata: input.standardMetadata ? {
        ...(field.standardMetadata as Record<string, any> || {}),
        ...input.standardMetadata,
        codeListDataType: codeList?.dataType || null,
      } : input.standardMetadata,
    },
  });
}

/**
 * 删除字段
 */
async function removeField(formId: string, fieldId: string) {
  const field = await prisma.crfFormField.findFirst({ where: { id: fieldId, formId } });
  if (!field) throw new NotFoundError('CrfFormField', fieldId);

  await prisma.crfFormField.delete({ where: { id: fieldId } });
  return { success: true };
}

/**
 * 创建编辑核查规则
 */
async function createEditCheckRule(formId: string, input: CreateEditCheckRuleInput, userId: string) {
  const form = await prisma.crfForm.findUnique({ where: { id: formId } });
  if (!form) throw new NotFoundError('CrfForm', formId);

  const existing = await prisma.crfEditCheckRule.findUnique({
    where: { formId_ruleCode: { formId, ruleCode: input.ruleCode } },
  });
  if (existing) throw new ConflictError('规则编码已存在');

  const rule = await prisma.crfEditCheckRule.create({
    data: {
      formId,
      ...input,
      targetFieldIds: input.targetFieldIds || [],
    },
  });

  logger.info('CRF edit check rule created', {
    audit: true,
    eventType: 'CRF_EDIT_CHECK_CREATE',
    projectId: form.projectId,
    message: `创建核查规则: ${input.ruleName}`,
  });

  return rule;
}

/**
 * 获取编辑核查规则列表
 */
async function getEditCheckRules(formId: string) {
  const form = await prisma.crfForm.findUnique({ where: { id: formId } });
  if (!form) throw new NotFoundError('CrfForm', formId);

  return prisma.crfEditCheckRule.findMany({
    where: { formId },
    orderBy: { createdAt: 'asc' },
  });
}

/**
 * 更新编辑核查规则
 */
async function updateEditCheckRule(formId: string, ruleId: string, input: Partial<CreateEditCheckRuleInput>) {
  const rule = await prisma.crfEditCheckRule.findFirst({ where: { id: ruleId, formId } });
  if (!rule) throw new NotFoundError('CrfEditCheckRule', ruleId);

  return prisma.crfEditCheckRule.update({
    where: { id: ruleId },
    data: input,
  });
}

/**
 * 删除编辑核查规则
 */
async function removeEditCheckRule(formId: string, ruleId: string) {
  const rule = await prisma.crfEditCheckRule.findFirst({ where: { id: ruleId, formId } });
  if (!rule) throw new NotFoundError('CrfEditCheckRule', ruleId);

  await prisma.crfEditCheckRule.delete({ where: { id: ruleId } });
  return { success: true };
}

/**
 * 发布表单（创建版本快照）
 */
async function publish(formId: string, input: PublishFormInput, userId: string) {
  const form = await prisma.crfForm.findUnique({
    where: { id: formId },
    include: {
      fields: { orderBy: { sortOrder: 'asc' } },
      editCheckRules: true,
    },
  });
  if (!form) throw new NotFoundError('CrfForm', formId);

  // 计算新版本号
  const versions = await prisma.crfFormVersion.findMany({
    where: { formId },
    orderBy: { createdAt: 'desc' },
    select: { version: true },
    take: 1,
  });

  const lastVersion = versions[0]?.version || '0.0';
  const parts = lastVersion.split('.');
  const newVersion = `${parseInt(parts[0] || '0') + 1}.0`;

  // 创建版本快照
  const version = await prisma.crfFormVersion.create({
    data: {
      formId,
      version: newVersion,
      changeLog: input.changeLog || `发布版本 ${newVersion}`,
      formData: {
        form: { formCode: form.formCode, formName: form.formName, formType: form.formType, description: form.description },
        fields: form.fields,
        editCheckRules: form.editCheckRules,
      },
      createdBy: userId,
    },
  });

  // 创建发布记录
  await prisma.crfFormPublication.create({
    data: {
      formId,
      version: newVersion,
      scopeType: input.scopeType || 'all',
      targetIds: input.targetIds || [],
      publishedBy: userId,
      effectiveDate: input.effectiveDate ? new Date(input.effectiveDate) : new Date(),
      notes: input.notes,
    },
  });

  // 更新表单状态
  await prisma.crfForm.update({
    where: { id: formId },
    data: {
      status: 'published',
      version: newVersion,
      publishedAt: new Date(),
      publishedBy: userId,
    },
  });

  logger.info('CRF form published', {
    audit: true,
    eventType: 'CRF_FORM_PUBLISH',
    projectId: form.projectId,
    message: `发布CRF表单: ${form.formName} 版本 ${newVersion}`,
  });

  return { formId, version: newVersion, publishedAt: new Date().toISOString() };
}

/**
 * 获取表单版本历史
 */
async function getVersions(formId: string) {
  const form = await prisma.crfForm.findUnique({ where: { id: formId } });
  if (!form) throw new NotFoundError('CrfForm', formId);

  return prisma.crfFormVersion.findMany({
    where: { formId },
    orderBy: { createdAt: 'desc' },
  });
}

/**
 * 获取特定版本详情
 */
async function getVersionDetail(formId: string, version: string) {
  const form = await prisma.crfForm.findUnique({ where: { id: formId } });
  if (!form) throw new NotFoundError('CrfForm', formId);

  const versionData = await prisma.crfFormVersion.findUnique({
    where: { formId_version: { formId, version } },
  });

  if (!versionData) throw new NotFoundError('CrfFormVersion', `${formId}/${version}`);
  return versionData;
}

/**
 * 获取发布记录
 */
async function getPublications(formId: string) {
  const form = await prisma.crfForm.findUnique({ where: { id: formId } });
  if (!form) throw new NotFoundError('CrfForm', formId);

  return prisma.crfFormPublication.findMany({
    where: { formId },
    orderBy: { publishedAt: 'desc' },
  });
}

export const formService = {
  create, getList, getById, update, remove,
  addField, updateField, removeField,
  createEditCheckRule, getEditCheckRules, updateEditCheckRule, removeEditCheckRule,
  publish, getVersions, getVersionDetail, getPublications,
};
