// 研究中心
export type SiteStatus = 'active' | 'inactive' | 'suspended' | 'closed';
export type EthicsStatus = 'pending' | 'approved' | 'rejected' | 'not_required';
export type ContractStatus = 'pending' | 'signed' | 'terminated';
export type RoleAtSite = 'PI' | 'SUB_I' | 'CRC' | 'CRA' | 'PHARMACIST' | 'NURSE' | 'OTHER';

export interface Site {
  id: string;
  projectId?: string;
  siteCode: string;
  siteName: string;
  address?: string;
  contactPhone?: string;
  ethicsStatus?: EthicsStatus;
  contractStatus?: ContractStatus;
  gcpContactName?: string;
  gcpContactPhone?: string;
  researchContactName?: string;
  researchContactPhone?: string;
  status?: SiteStatus;
  createdAt: string;
  updatedAt: string;
  siteStaff?: SiteStaff[];
}

export interface CreateSiteParams {
  projectId?: string;
  siteCode: string;
  siteName: string;
  piUserId?: string;
  address?: string;
  contactPhone?: string;
  ethicsStatus?: EthicsStatus;
  contractStatus?: ContractStatus;
  gcpContactName?: string;
  gcpContactPhone?: string;
  researchContactName?: string;
  researchContactPhone?: string;
}

export type UpdateSiteParams = Partial<CreateSiteParams> & {
  status?: SiteStatus;
};

// 中心工作人员
export interface SiteStaff {
  id: string;
  siteId: string;
  userId: string;
  roleAtSite: RoleAtSite;
  joinedAt?: string;
  leftAt?: string;
  status?: 'active' | 'inactive';
  user?: {
    id: string;
    username: string;
    displayName?: string;
    email?: string;
  };
}

export interface AddSiteStaffParams {
  userId: string;
  roleAtSite: RoleAtSite;
  joinedAt?: string;
}

export type UpdateSiteStaffParams = Partial<AddSiteStaffParams> & {
  leftAt?: string;
  status?: 'active' | 'inactive';
};
