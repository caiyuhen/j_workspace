import { z } from 'zod';

// ========== CRF 表单 DTO ==========

export const createFieldSchema = z.object({
  fieldCode: z.string().min(1).max(100),
  fieldName: z.string().min(1).max(200),
  fieldType: z.enum(['text', 'textarea', 'number', 'date', 'time', 'datetime', 'boolean', 'radio', 'checkbox', 'select', 'multiselect', 'file', 'calculated', 'signature']),
  controlType: z.enum(['input', 'textarea', 'number_input', 'date_picker', 'time_picker', 'datetime_picker', 'radio_group', 'checkbox_group', 'select', 'multiselect', 'yes_no', 'codelist_select', 'dictionary_lookup', 'file_upload', 'signature_pad', 'derived', 'hidden']).optional().default('input'),
  description: z.string().max(500).optional(),
  placeholder: z.string().max(200).optional(),
  questionText: z.string().max(500).optional(),
  defaultValue: z.string().optional(),
  required: z.boolean().optional().default(false),
  maxLength: z.number().int().positive().optional(),
  minValue: z.number().optional(),
  maxValue: z.number().optional(),
  displayFormat: z.string().max(100).optional(),
  origin: z.enum(['crf', 'epro', 'device', 'derived', 'central_lab', 'vendor', 'other']).optional(),
  validationRegex: z.string().max(500).optional(),
  options: z.array(z.object({
    label: z.string(),
    value: z.string(),
    code: z.string().optional(),
  })).optional().default([]),
  unit: z.string().max(50).optional(),
  sortOrder: z.number().int().optional().default(0),
  parentFieldId: z.string().uuid().optional(),
  cdiscDomain: z.string().min(2).max(10).optional(),
  cdashDataset: z.string().max(50).optional(),
  cdashVariable: z.string().max(40).optional(),
  cdashDataType: z.string().max(20).optional(),
  codeListOid: z.string().max(100).optional(),
  cdashPrompt: z.string().max(500).optional(),
  sdtmVariable: z.string().max(40).optional(),
  sdtmRole: z.string().max(20).optional(),
  implementationClass: z.string().max(50).optional(),
  standardMetadata: z.record(z.any()).optional(),
  dependencyRule: z.object({
    type: z.enum(['show', 'hide', 'enable', 'disable', 'calculate']),
    triggerFieldId: z.string(),
    condition: z.record(z.any()).optional(),
    expression: z.string().optional(),
  }).optional(),
});

export const createFormSchema = z.object({
  projectId: z.string().uuid(),
  formCode: z.string().min(1, '表单编码不能为空').max(100),
  formName: z.string().min(1, '表单名称不能为空').max(200),
  formType: z.enum(['informed_consent', 'enrollment', 'screening', 'visit', 'unscheduled', 'follow_up', 'end_of_study', 'other']),
  standardName: z.enum(['CDASH', 'CDISC']).optional().default('CDASH'),
  standardVersion: z.string().min(1).max(20).optional().default('2.1'),
  cdiscDomain: z.string().min(2).max(10).optional(),
  cdashModel: z.string().max(50).optional(),
  sdtmDatasetName: z.string().max(10).optional(),
  implementationGuide: z.string().max(100).optional(),
  description: z.string().optional(),
  formMetadata: z.record(z.any()).optional(),
  isRepeating: z.boolean().optional().default(false),
  maxRepeats: z.number().int().positive().optional(),
  visitWindow: z.string().max(100).optional(),
  sortOrder: z.number().int().optional().default(0),
  fields: z.array(createFieldSchema).optional(),
});

export type CreateFormInput = z.infer<typeof createFormSchema>;
export type CreateFieldInput = z.infer<typeof createFieldSchema>;

export const updateFormSchema = z.object({
  formName: z.string().min(1).max(200).optional(),
  standardName: z.enum(['CDASH', 'CDISC']).optional(),
  standardVersion: z.string().min(1).max(20).optional(),
  cdiscDomain: z.string().min(2).max(10).optional(),
  cdashModel: z.string().max(50).optional(),
  sdtmDatasetName: z.string().max(10).optional(),
  implementationGuide: z.string().max(100).optional(),
  description: z.string().optional(),
  formMetadata: z.record(z.any()).optional(),
  isRepeating: z.boolean().optional(),
  maxRepeats: z.number().int().positive().optional(),
  visitWindow: z.string().max(100).optional(),
  sortOrder: z.number().int().optional(),
});
export type UpdateFormInput = z.infer<typeof updateFormSchema>;

export const addFieldSchema = z.object({
  fieldCode: z.string().min(1).max(100),
  fieldName: z.string().min(1).max(200),
  fieldType: z.enum(['text', 'textarea', 'number', 'date', 'time', 'datetime', 'boolean', 'radio', 'checkbox', 'select', 'multiselect', 'file', 'calculated', 'signature']),
  controlType: z.enum(['input', 'textarea', 'number_input', 'date_picker', 'time_picker', 'datetime_picker', 'radio_group', 'checkbox_group', 'select', 'multiselect', 'yes_no', 'codelist_select', 'dictionary_lookup', 'file_upload', 'signature_pad', 'derived', 'hidden']).optional().default('input'),
  description: z.string().max(500).optional(),
  placeholder: z.string().max(200).optional(),
  questionText: z.string().max(500).optional(),
  defaultValue: z.string().optional(),
  required: z.boolean().optional().default(false),
  maxLength: z.number().int().positive().optional(),
  minValue: z.number().optional(),
  maxValue: z.number().optional(),
  displayFormat: z.string().max(100).optional(),
  origin: z.enum(['crf', 'epro', 'device', 'derived', 'central_lab', 'vendor', 'other']).optional(),
  validationRegex: z.string().max(500).optional(),
  options: z.array(z.object({
    label: z.string(),
    value: z.string(),
    code: z.string().optional(),
  })).optional().default([]),
  unit: z.string().max(50).optional(),
  sortOrder: z.number().int().optional().default(0),
  parentFieldId: z.string().uuid().optional(),
  cdiscDomain: z.string().min(2).max(10).optional(),
  cdashDataset: z.string().max(50).optional(),
  cdashVariable: z.string().max(40).optional(),
  cdashDataType: z.string().max(20).optional(),
  codeListOid: z.string().max(100).optional(),
  cdashPrompt: z.string().max(500).optional(),
  sdtmVariable: z.string().max(40).optional(),
  sdtmRole: z.string().max(20).optional(),
  implementationClass: z.string().max(50).optional(),
  standardMetadata: z.record(z.any()).optional(),
  dependencyRule: z.any().optional(),
});
export type AddFieldInput = z.infer<typeof addFieldSchema>;

export const createEditCheckRuleSchema = z.object({
  ruleCode: z.string().min(1).max(100),
  ruleName: z.string().min(1).max(200),
  ruleType: z.enum(['range_check', 'consistency_check', 'skip_logic', 'calculation', 'custom']),
  description: z.string().optional(),
  expression: z.string().min(1, '规则表达式不能为空'),
  errorMessage: z.string().min(1, '错误消息不能为空').max(500),
  severity: z.enum(['info', 'warning', 'error', 'hard_stop']).optional().default('warning'),
  targetFieldIds: z.array(z.string()).optional().default([]),
  isActive: z.boolean().optional().default(true),
});
export type CreateEditCheckRuleInput = z.infer<typeof createEditCheckRuleSchema>;

export const publishFormSchema = z.object({
  changeLog: z.string().optional(),
  scopeType: z.enum(['all', 'specific_sites']).optional().default('all'),
  targetIds: z.array(z.string()).optional().default([]),
  effectiveDate: z.string().datetime().optional(),
  notes: z.string().optional(),
});
export type PublishFormInput = z.infer<typeof publishFormSchema>;

export const addFieldSchemaFinal = z.object({
  fieldCode: z.string().min(1).max(100),
  fieldName: z.string().min(1).max(200),
  fieldType: z.enum(['text', 'textarea', 'number', 'date', 'time', 'datetime', 'boolean', 'radio', 'checkbox', 'select', 'multiselect', 'file', 'calculated', 'signature']),
  controlType: z.enum(['input', 'textarea', 'number_input', 'date_picker', 'time_picker', 'datetime_picker', 'radio_group', 'checkbox_group', 'select', 'multiselect', 'yes_no', 'codelist_select', 'dictionary_lookup', 'file_upload', 'signature_pad', 'derived', 'hidden']).optional().default('input'),
  description: z.string().max(500).optional(),
  placeholder: z.string().max(200).optional(),
  questionText: z.string().max(500).optional(),
  defaultValue: z.string().optional(),
  required: z.boolean().optional().default(false),
  maxLength: z.number().int().positive().optional(),
  minValue: z.number().optional(),
  maxValue: z.number().optional(),
  displayFormat: z.string().max(100).optional(),
  origin: z.enum(['crf', 'epro', 'device', 'derived', 'central_lab', 'vendor', 'other']).optional(),
  validationRegex: z.string().max(500).optional(),
  options: z.array(z.object({ label: z.string(), value: z.string(), code: z.string().optional() })).optional().default([]),
  unit: z.string().max(50).optional(),
  sortOrder: z.number().int().optional().default(0),
  parentFieldId: z.string().uuid().optional(),
  cdiscDomain: z.string().min(2).max(10).optional(),
  cdashDataset: z.string().max(50).optional(),
  cdashVariable: z.string().max(40).optional(),
  cdashDataType: z.string().max(20).optional(),
  codeListOid: z.string().max(100).optional(),
  cdashPrompt: z.string().max(500).optional(),
  sdtmVariable: z.string().max(40).optional(),
  sdtmRole: z.string().max(20).optional(),
  implementationClass: z.string().max(50).optional(),
  standardMetadata: z.record(z.any()).optional(),
  dependencyRule: z.any().optional(),
});
export type AddFieldInputFinal = z.infer<typeof addFieldSchemaFinal>;
