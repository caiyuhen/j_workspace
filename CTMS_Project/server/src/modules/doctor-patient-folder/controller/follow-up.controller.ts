import { Request, Response, NextFunction } from 'express';
import { FollowUpService } from '../service/follow-up.service';
import { createFollowUpSchema, updateFollowUpSchema } from '../dto/follow-up.dto';

const followUpService = new FollowUpService();

export class FollowUpController {
  async createFollowUp(req: Request, res: Response, next: NextFunction) {
    try {
      const data = createFollowUpSchema.parse(req.body);
      const result = await followUpService.createFollowUp(data);
      res.status(201).json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async getFollowUp(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await followUpService.getFollowUpById(req.params.id);
      if (!result) {
        return res.status(404).json({ success: false, message: 'Follow-up not found' });
      }
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async updateFollowUp(req: Request, res: Response, next: NextFunction) {
    try {
      const data = updateFollowUpSchema.parse(req.body);
      const result = await followUpService.updateFollowUp(req.params.id, data);
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async deleteFollowUp(req: Request, res: Response, next: NextFunction) {
    try {
      await followUpService.deleteFollowUp(req.params.id);
      res.json({ success: true, message: 'Follow-up deleted successfully' });
    } catch (error) {
      next(error);
    }
  }

  async getFollowUpsByPatient(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await followUpService.getFollowUpsByPatient(req.params.patientId);
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }
}
