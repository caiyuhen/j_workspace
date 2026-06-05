// ==================== 文档管理 (TMF) ====================

export interface Document {
  id: string;
  projectId: string;
  category: string;
  subCategory?: string;
  documentNumber: string;
  title: string;
  version: number;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'superseded' | 'archived';
  documentType: 'TMF' | 'ISF' | 'ICF' | 'CSR' | 'Protocol' | 'Other';
  fileName?: string;
  fileSize?: number;
  mimeType?: string;
  fileUrl?: string;
  effectiveDate?: string;
  expiryDate?: string;
  authorId?: string;
  reviewerId?: string;
  approverId?: string;
  description?: string;
  tags?: string[];
  isRequired: boolean;
  isCompleted: boolean;
  createdAt: string;
  updatedAt: string;
  author?: { id: string; displayName: string };
  currentVersion?: DocumentVersion;
}

export interface CreateDocumentParams {
  projectId: string;
  category: string;
  subCategory?: string;
  documentNumber: string;
  title: string;
  documentType: 'TMF' | 'ISF' | 'ICF' | 'CSR' | 'Protocol' | 'Other';
  effectiveDate?: string;
  expiryDate?: string;
  description?: string;
  tags?: string[];
  isRequired?: boolean;
}

export interface DocumentVersion {
  id: string;
  documentId: string;
  version: number;
  fileName: string;
  fileSize: number;
  mimeType: string;
  fileUrl: string;
  changeSummary?: string;
  uploadedById: string;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected';
  createdAt: string;
  uploadedBy?: { id: string; displayName: string };
}

export interface DocumentStats {
  total: number;
  completed: number;
  pending: number;
  overdue: number;
  byCategory: { category: string; total: number; completed: number }[];
}
