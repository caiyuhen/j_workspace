import prisma from '../../../config/database';
import { CreateTemplateInput, UpdateTemplateInput } from '../dto/template.dto';

export class TemplateService {
  async getAllTemplates() {
    return await prisma.doctorFormTemplate.findMany({
      where: { usedInDoctorFolder: true },
      orderBy: { createdAt: 'desc' }
    });
  }

  async getTemplateById(id: string) {
    return await prisma.doctorFormTemplate.findUnique({
      where: { id }
    });
  }

  async createTemplate(createTemplateDto: CreateTemplateInput) {
    return await prisma.doctorFormTemplate.create({
      data: createTemplateDto
    });
  }

  async updateTemplate(id: string, updateTemplateDto: UpdateTemplateInput) {
    return await prisma.doctorFormTemplate.update({
      where: { id },
      data: updateTemplateDto
    });
  }

  async deleteTemplate(id: string) {
    await prisma.doctorFormTemplate.delete({
      where: { id }
    });
  }
}
