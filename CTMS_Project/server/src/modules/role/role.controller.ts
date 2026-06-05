import { Request, Response, NextFunction } from 'express';
import { roleService } from './role.service';
import { createRoleSchema, updateRoleSchema, assignPermissionsSchema } from './role.dto';

// POST / - 创建角色
async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createRoleSchema.parse(req.body);
    const result = await roleService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET / - 角色列表
async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await roleService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /permissions - 所有权限列表
async function listPermissions(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await roleService.listAllPermissions();
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /:id - 角色详情
async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await roleService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// PUT /:id - 更新角色
async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateRoleSchema.parse(req.body);
    const result = await roleService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// DELETE /:id - 删除角色
async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await roleService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// POST /:id/permissions - 分配权限
async function assignPermissions(req: Request, res: Response, next: NextFunction) {
  try {
    const input = assignPermissionsSchema.parse(req.body);
    const result = await roleService.assignPermissions(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /:id/users - 获取角色下的用户
async function getRoleUsers(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await roleService.getRoleUsers(req.params.id, req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const roleController = {
  create, list, listPermissions, getById, update, remove, assignPermissions, getRoleUsers,
};
