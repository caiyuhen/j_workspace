import { Request, Response, NextFunction } from 'express';
import { TemplateService } from '../service/template.service';
import { createTemplateSchema, updateTemplateSchema } from '../dto/template.dto';

const templateService = new TemplateService();

export class TemplateController {
  async getAllTemplates(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await templateService.getAllTemplates();
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async getTemplate(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await templateService.getTemplateById(req.params.id);
      if (!result) {
        return res.status(404).json({ success: false, message: 'Template not found' });
      }
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async createTemplate(req: Request, res: Response, next: NextFunction) {
    try {
      const data = createTemplateSchema.parse(req.body);
      const result = await templateService.createTemplate(data);
      res.status(201).json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async updateTemplate(req: Request, res: Response, next: NextFunction) {
    try {
      const data = updateTemplateSchema.parse(req.body);
      const result = await templateService.updateTemplate(req.params.id, data);
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async deleteTemplate(req: Request, res: Response, next: NextFunction) {
    try {
      await templateService.deleteTemplate(req.params.id);
      res.json({ success: true, message: 'Template deleted successfully' });
    } catch (error) {
      next(error);
    }
  }
}
