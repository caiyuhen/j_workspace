import prisma from '../../../config/database';
import { CreatePatientInput, UpdatePatientInput } from '../dto/patient.dto';

export class PatientService {
  async createPatient(createPatientDto: CreatePatientInput, doctorId: string) {
    const data: any = { ...createPatientDto, doctorId };
    if (data.dateOfBirth) {
      data.dateOfBirth = new Date(data.dateOfBirth);
    }
    
    return await prisma.doctorPatientRecord.create({
      data
    });
  }

  async getPatientById(id: string) {
    return await prisma.doctorPatientRecord.findUnique({
      where: { id },
      include: { followUpRecords: true }
    });
  }

  async updatePatient(id: string, updatePatientDto: UpdatePatientInput) {
    const data: any = { ...updatePatientDto };
    if (data.dateOfBirth) {
      data.dateOfBirth = new Date(data.dateOfBirth);
    }

    return await prisma.doctorPatientRecord.update({
      where: { id },
      data
    });
  }

  async deletePatient(id: string) {
    await prisma.doctorPatientRecord.delete({
      where: { id }
    });
  }

  async getPatientsByDoctor(doctorId: string) {
    return await prisma.doctorPatientRecord.findMany({
      where: { doctorId },
      orderBy: { createdAt: 'desc' }
    });
  }
}
