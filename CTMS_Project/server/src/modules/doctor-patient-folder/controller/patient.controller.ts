import { Request, Response, NextFunction } from 'express';
import { PatientService } from '../service/patient.service';
import { createPatientSchema, updatePatientSchema } from '../dto/patient.dto';

const patientService = new PatientService();

export class PatientController {
  async createPatient(req: Request, res: Response, next: NextFunction) {
    try {
      const data = createPatientSchema.parse(req.body);
      const doctorId = (req as any).user?.userId || 'current-user-id'; // Fallback if auth is missing
      const result = await patientService.createPatient(data, doctorId);
      res.status(201).json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async getPatient(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await patientService.getPatientById(req.params.id);
      if (!result) {
        return res.status(404).json({ success: false, message: 'Patient not found' });
      }
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async updatePatient(req: Request, res: Response, next: NextFunction) {
    try {
      const data = updatePatientSchema.parse(req.body);
      const result = await patientService.updatePatient(req.params.id, data);
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }

  async deletePatient(req: Request, res: Response, next: NextFunction) {
    try {
      await patientService.deletePatient(req.params.id);
      res.json({ success: true, message: 'Patient deleted successfully' });
    } catch (error) {
      next(error);
    }
  }

  async getPatients(req: Request, res: Response, next: NextFunction) {
    try {
      const doctorId = (req as any).user?.userId || 'current-user-id';
      const result = await patientService.getPatientsByDoctor(doctorId);
      res.json({ success: true, data: result });
    } catch (error) {
      next(error);
    }
  }
}
