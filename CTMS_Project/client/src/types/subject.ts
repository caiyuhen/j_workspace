// 受试者
export type EnrollmentStatus = 'screening' | 'enrolled' | 'randomized' | 'ongoing' | 'completed' | 'discontinued' | 'withdrawn';

export interface Subject {
  id: string;
  projectId: string;
  siteId?: string;
  subjectCode: string;
  screeningNumber?: string;
  enrollmentStatus: EnrollmentStatus;
  discontinuationReason?: string;
  randomizationNumber?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSubjectParams {
  projectId: string;
  siteId?: string;
  subjectCode: string;
  screeningNumber?: string;
  enrollmentStatus?: EnrollmentStatus;
}

export type UpdateSubjectParams = Partial<CreateSubjectParams> & {
  discontinuationReason?: string;
  randomizationNumber?: string;
};

// 访视
export interface Visit {
  id: string;
  subjectId: string;
  visitCode: string;
  visitName: string;
  plannedDate: string;
  actualDate?: string;
  status?: string;
  siteId?: string;
}

export interface CreateVisitParams {
  visitCode: string;
  visitName: string;
  plannedDate: string;
  siteId?: string;
}
