// randomization.dto.ts - 随机化管理数据传输对象

export interface CreateRandomizationDto {
  subjectId: string;
  projectId: string;
  randomizationNumber: string;
  treatmentArm?: string;
  randomizationDate: string; // ISO date string
  method?: string;
  stratifiedFactors?: Record<string, any>;
  drugBatch?: string;
  drugExpiryDate?: string; // ISO date string
}

export interface RandomizationQueryDto {
  projectId?: string;
  treatmentArm?: string;
  method?: string;
  page?: number;
  pageSize?: number;
}
