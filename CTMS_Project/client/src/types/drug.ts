// ==================== 药物管理 ====================

export interface Drug {
  id: string;
  projectId: string;
  drugName: string;
  drugCode: string;
  dosageForm: string;
  strength: string;
  manufacturer: string;
  lotNumber?: string;
  expiryDate?: string;
  storageCondition: string;
  blindStatus: 'blinded' | 'unblinded' | 'partially_blinded';
  status: 'active' | 'inactive' | 'recall' | 'destroyed';
  createdAt: string;
  updatedAt: string;
}

export interface CreateDrugParams {
  projectId: string;
  drugName: string;
  drugCode: string;
  dosageForm: string;
  strength: string;
  manufacturer: string;
  lotNumber?: string;
  expiryDate?: string;
  storageCondition: string;
  blindStatus: 'blinded' | 'unblinded' | 'partially_blinded';
}

export interface SupplyPlan {
  id: string;
  drugId: string;
  siteId: string;
  plannedQuantity: number;
  actualQuantity?: number;
  plannedDate: string;
  actualDate?: string;
  status: 'planned' | 'shipped' | 'received' | 'cancelled';
  createdAt: string;
}

export interface Shipment {
  id: string;
  drugId: string;
  fromSiteId?: string;
  toSiteId: string;
  quantity: number;
  shippedDate?: string;
  receivedDate?: string;
  trackingNumber?: string;
  status: 'pending' | 'shipped' | 'in_transit' | 'received' | 'returned';
  temperatureLog?: string;
  remarks?: string;
  createdAt: string;
}

export interface Inventory {
  id: string;
  drugId: string;
  siteId: string;
  quantityOnHand: number;
  quantityDispensed: number;
  quantityReturned: number;
  quantityDestroyed: number;
  lastCountDate?: string;
  remarks?: string;
  updatedAt: string;
}

export interface Destruction {
  id: string;
  drugId: string;
  siteId: string;
  quantity: number;
  reason: string;
  method: string;
  destructionDate: string;
  witnessId?: string;
  certificateNumber?: string;
  status: 'pending' | 'completed' | 'cancelled';
  createdAt: string;
}
