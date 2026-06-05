import { Router } from 'express';
import { PatientController } from '../controller/patient.controller';
import { FollowUpController } from '../controller/follow-up.controller';
import { TemplateController } from '../controller/template.controller';

const router = Router();
const patientController = new PatientController();
const followUpController = new FollowUpController();
const templateController = new TemplateController();

// 患者相关路由
router.post('/', patientController.createPatient);
router.get('/:id', patientController.getPatient);
router.put('/:id', patientController.updatePatient);
router.delete('/:id', patientController.deletePatient);
router.get('/', patientController.getPatients);

// 随访相关路由
router.post('/follow-up', followUpController.createFollowUp);
router.get('/follow-up/:id', followUpController.getFollowUp);
router.put('/follow-up/:id', followUpController.updateFollowUp);
router.delete('/follow-up/:id', followUpController.deleteFollowUp);
router.get('/follow-up/patient/:patientId', followUpController.getFollowUpsByPatient);

// 模板相关路由
router.post('/templates', templateController.createTemplate);
router.get('/templates', templateController.getAllTemplates);
router.get('/templates/:id', templateController.getTemplate);
router.put('/templates/:id', templateController.updateTemplate);
router.delete('/templates/:id', templateController.deleteTemplate);

export default router;