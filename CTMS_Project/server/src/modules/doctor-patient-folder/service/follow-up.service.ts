import prisma from '../../../config/database';
import { CreateFollowUpInput, UpdateFollowUpInput } from '../dto/follow-up.dto';

export class FollowUpService {
  async createFollowUp(createFollowUpDto: CreateFollowUpInput) {
    const data: any = { ...createFollowUpDto };
    if (data.visitDate) {
      data.visitDate = new Date(data.visitDate);
    }
    
    return await prisma.doctorFollowUpRecord.create({
      data
    });
  }

  async getFollowUpsByPatient(patientId: string) {
    return await prisma.doctorFollowUpRecord.findMany({
      where: { patientRecordId: patientId },
      orderBy: { visitDate: 'desc' }
    });
  }

  async getFollowUpById(id: string) {
    return await prisma.doctorFollowUpRecord.findUnique({
      where: { id },
      include: { patientRecord: true }
    });
  }

  async updateFollowUp(id: string, updateFollowUpDto: UpdateFollowUpInput) {
    const data: any = { ...updateFollowUpDto };
    if (data.visitDate) {
      data.visitDate = new Date(data.visitDate);
    }

    return await prisma.doctorFollowUpRecord.update({
      where: { id },
      data
    });
  }

  async deleteFollowUp(id: string) {
    await prisma.doctorFollowUpRecord.delete({
      where: { id }
    });
  }
}
