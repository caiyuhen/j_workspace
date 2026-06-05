import { Request, Response, NextFunction } from 'express';
import { abacService } from './abac.service';
import { CreateAbacPolicyInput, UpdateAbacPolicyInput } from './abac.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input: CreateAbacPolicyInput = req.body;
    const result = await abacService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await abacService.getList(req.query as any);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await abacService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input: UpdateAbacPolicyInput = req.body;
    const result = await abacService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await abacService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function evaluate(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await abacService.evaluateAccess(req.body);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function batchEvaluate(req: Request, res: Response, next: NextFunction) {
  try {
    const { userId, checks } = req.body;
    const result = await abacService.batchEvaluate(userId, checks);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getEffectivePolicies(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await abacService.getEffectivePolicies(
      req.params.resource,
      req.query.action as string | undefined,
    );
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const abacController = {
  create, list, getById, update, remove,
  evaluate, batchEvaluate, getEffectivePolicies,
};
