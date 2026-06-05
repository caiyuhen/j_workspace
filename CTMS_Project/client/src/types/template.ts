// CRF 模板
export type TemplateType = 'crf' | 'ae_report' | 'lab_result' | 'visit_note' | 'consent' | 'other';
export type TemplateStatus = 'draft' | 'published' | 'deprecated' | 'archived';

export interface EdcTemplate {
  id: string;
  templateCode: string;
  templateName: string;
  templateType: TemplateType;
  version: string;
  templateData?: Record<string, any>;
  description?: string;
  projectId?: string;
  cdiscDomain?: string;
  status: TemplateStatus;
  isSystemTemplate?: boolean;
  isShared?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTemplateParams {
  templateCode: string;
  templateName: string;
  templateType: TemplateType;
  version: string;
  templateData?: Record<string, any>;
  description?: string;
  projectId?: string;
  cdiscDomain?: string;
  isSystemTemplate?: boolean;
  isShared?: boolean;
}

export type UpdateTemplateParams = Partial<CreateTemplateParams> & {
  status?: TemplateStatus;
};

export interface CloneTemplateParams {
  newTemplateCode: string;
  newTemplateName: string;
  newVersion?: string;
  projectId?: string;
}
