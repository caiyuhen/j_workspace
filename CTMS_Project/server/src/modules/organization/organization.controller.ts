import { Request, Response, NextFunction } from 'express';
import { organizationService } from './organization.service';
import { createOrgSchema, updateOrgSchema } from './organization.dto';

// POST / - 创建组织
async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createOrgSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await organizationService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET / - 组织列表
async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await organizationService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /tree - 组织树形结构
async function tree(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await organizationService.getTree(req.query.orgType as string);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /:id - 组织详情
async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await organizationService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// PUT /:id - 更新组织
async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateOrgSchema.parse(req.body);
    const result = await organizationService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// DELETE /:id - 停用组织
async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await organizationService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const organizationController = {
  create, list, tree, getById, update, remove,
};
