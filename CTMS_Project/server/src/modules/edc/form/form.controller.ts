import { Request, Response, NextFunction } from 'express';
import { formService } from './form.service';
import {
  createFormSchema, updateFormSchema,
  addFieldSchemaFinal, createEditCheckRuleSchema,
  publishFormSchema,
} from './form.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createFormSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await formService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateFormSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await formService.update(req.params.id, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 字段管理
async function addField(req: Request, res: Response, next: NextFunction) {
  try {
    const input = addFieldSchemaFinal.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await formService.addField(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateField(req: Request, res: Response, next: NextFunction) {
  try {
    const input = addFieldSchemaFinal.partial().parse(req.body);
    const result = await formService.updateField(req.params.id, req.params.fieldId, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function removeField(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.removeField(req.params.id, req.params.fieldId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 编辑核查规则
async function createEditCheckRule(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createEditCheckRuleSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await formService.createEditCheckRule(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getEditCheckRules(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.getEditCheckRules(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateEditCheckRule(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createEditCheckRuleSchema.partial().parse(req.body);
    const result = await formService.updateEditCheckRule(req.params.id, req.params.ruleId, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function removeEditCheckRule(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.removeEditCheckRule(req.params.id, req.params.ruleId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 版本与发布
async function publish(req: Request, res: Response, next: NextFunction) {
  try {
    const input = publishFormSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await formService.publish(req.params.id, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getVersions(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.getVersions(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getVersionDetail(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.getVersionDetail(req.params.id, req.params.version);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getPublications(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await formService.getPublications(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const formController = {
  create, list, getById, update, remove,
  addField, updateField, removeField,
  createEditCheckRule, getEditCheckRules, updateEditCheckRule, removeEditCheckRule,
  publish, getVersions, getVersionDetail, getPublications,
};
