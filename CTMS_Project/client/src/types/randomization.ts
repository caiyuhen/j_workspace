// ==================== 随机化管理 ====================

export interface RandomizationRecord {
  id: string;
  projectId: string;
  subjectId: string;
  randomizationNumber: string;
  treatmentArm: string;
  stratum?: string;
  siteId: string;
  randomizationDate: string;
  randomizedById: string;
  isUnblinded: boolean;
  unblindedAt?: string;
  unblindedById?: string;
  unblindReason?: string;
  status: 'randomized' | 'unblinded' | 'cancelled';
  createdAt: string;
  updatedAt: string;
  subject?: { id: string; subjectCode: string };
  randomizedBy?: { id: string; displayName: string };
  site?: { id: string; name: string };
}

export interface CreateRandomizationParams {
  projectId: string;
  subjectId: string;
  siteId: string;
  stratum?: string;
}

export interface EmergencyUnblindParams {
  subjectId: string;
  reason: string;
}

export interface RandomizationStats {
  projectId: string;
  totalRandomized: number;
  totalUnblinded: number;
  armDistribution: { arm: string; count: number; percentage: number }[];
  bySite: { siteId: string; siteName: string; count: number }[];
  poolStatus: {
    total: number;
    used: number;
    remaining: number;
    byStratum: { stratum: string; total: number; used: number; remaining: number }[];
  };
}

export interface NumberPoolStatus {
  projectId: string;
  total: number;
  used: number;
  remaining: number;
  byStratum: { stratum: string; total: number; used: number; remaining: number }[];
}
