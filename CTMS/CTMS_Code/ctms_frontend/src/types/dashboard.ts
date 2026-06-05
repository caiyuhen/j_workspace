export interface DashboardStats {
  trials: {
    total: number;
    active: number;
  };
  subjects: {
    total: number;
    active: number;
    enrolled: number;
  };
  safety: {
    pending_saes: number;
  };
  sites: {
    total: number;
    active: number;
  };
  charts: {
    recruitment_trend: Array<{ name: string; subjects: number }>;
    site_distribution: Array<{ name: string; value: number }>;
    ae_severity: Array<{ name: string; value: number }>;
    query_status: Array<{ name: string; value: number }>;
    visit_status: Array<{ name: string; value: number }>;
    deviation_status: Array<{ name: string; value: number }>;
    monitoring_status: Array<{ name: string; value: number }>;
  };
}
