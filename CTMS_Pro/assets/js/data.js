<<<<<<< HEAD
// CTMS 系统模拟数据 (Mock data cleared, relying purely on PostgreSQL)
const CTMS_DATA = {
  currentUser: { name: '用户', role: '-', dept: '-', avatar: 'U' },
  
  trials: [],
  patients: [],
  drugs: [],
  drugLogs: [],
  contracts: [],
  milestones: [],
  saeEvents: [],
  visits: [],
  auditLogs: [],
  qcRecords: [],
  announcements: [],
  centerStats: [],
  enrollTrend: [],
  documents: [],
  users: [],
  timesheets: []
};

// 辅助函数
function getTrialById(id) { return CTMS_DATA.trials.find(t => t.id === id); }
function getPatientsByTrial(trialId) { return CTMS_DATA.patients.filter(p => p.trialId === trialId); }
function getStatusLabel(status) {
  const map = { running: '进行中', startup: '启动期', closing: '结题中', done: '已完成', pending: '待完成', screen_fail: '筛选失败', enrolled: '已入组', screening: '筛选中', dropout: '脱落', active: '生效中', normal: '正常', warning: '近效期' };
  return map[status] || status;
}
function getStatusBadge(status) {
  const map = { running: 'badge-green', startup: 'badge-blue', closing: 'badge-yellow', done: 'badge-gray', pending: 'badge-yellow', screen_fail: 'badge-red', enrolled: 'badge-green', screening: 'badge-blue', dropout: 'badge-gray', active: 'badge-green', normal: 'badge-green', warning: 'badge-yellow' };
  return map[status] || 'badge-gray';
}
function formatDate(d) { if (!d) return '-'; return d; }
function calcDays(d1, d2) { if (!d1 || !d2) return 0; return Math.round((new Date(d2) - new Date(d1)) / 86400000); }

function mapTrialStatus(status) {
  const m = {
    ONGOING: 'running',
    RECRUITING: 'running',
    PLANNING: 'startup',
    INITIATING: 'startup',
    COMPLETED: 'done',
    TERMINATED: 'closing',
    SUSPENDED: 'closing',
  };
  return m[status] || 'running';
}

function mapPatientStatus(status) {
  const m = {
    ENROLLED: 'enrolled',
    SCREENING: 'screening',
    SCREEN_FAIL: 'screen_fail',
    SCREEN_FAILED: 'screen_fail',
    WITHDRAWN: 'dropout',
    COMPLETED: 'done',
    ACTIVE: 'enrolled',
  };
  return m[status] || 'screening';
}

async function syncCTMSDataFromPostgreSQL() {
  if (!window.CTMS_API || !CTMS_API.Token.getAccessToken()) return false;

  const results = await Promise.allSettled([
      CTMS_API.Trial.list({ page: 1, page_size: 100 }),
      CTMS_API.Patient.list({ page: 1, page_size: 100 }),
      CTMS_API.Visit.list({ page: 1, page_size: 500 }),
      CTMS_API.AE.list({}),
      CTMS_API.Drug.listBatches({}),
      CTMS_API.Finance.listContracts({}),
      CTMS_API.Notification.list({ page: 1, page_size: 50 }),
      CTMS_API.Report.enrollmentTrend({ months: 12 }),
      window.API.sites.list({ page: 1, page_size: 500 }),
      CTMS_API.Document.list({ page: 1, page_size: 500 }),
      CTMS_API.IWRS.listSchemes({ page: 1, page_size: 100 }),
      CTMS_API.IWRS.listRandomizations({ page: 1, page_size: 100 }),
      window.API.drugs.listLogs({ limit: 50 }),
      window.API.users.list({ page: 1, page_size: 100 }),
      window.API.timesheets.list({ page: 1, page_size: 500 }),
      fetch(window.API_BASE_URL + '/roles', { headers: { 'Authorization': 'Bearer ' + localStorage.getItem('access_token') } }).then(r => r.json())
    ]);

  const [trialsRes, patientsRes, visitsRes, aeRes, drugsRes, contractsRes, notifRes, trendRes, sitesRes, docsRes, iwrsSchemesRes, iwrsSubjectsRes, drugLogsRes, usersRes, timesheetsRes, rolesRes2] = results;

  const trialsRaw = trialsRes.status === 'fulfilled' ? (trialsRes.value.items || []) : [];
  const trialIdToNo = {};
  
  const patientsRaw = patientsRes.status === 'fulfilled' ? (patientsRes.value.items || []) : [];
  const patientIdToNo = {};
  
  // Calculate real enrolled count and center count per trial from patients list
  const trialEnrolledCounts = {};
  const trialCenterSets = {};
  patientsRaw.forEach(p => {
    const tId = String(p.trial_id || '');
    if (mapPatientStatus(p.status) === 'enrolled') {
      trialEnrolledCounts[tId] = (trialEnrolledCounts[tId] || 0) + 1;
    }
    if (p.site_id) {
      if (!trialCenterSets[tId]) trialCenterSets[tId] = new Set();
      trialCenterSets[tId].add(p.site_id);
    }
  });

  CTMS_DATA.trials = trialsRaw.map((t) => {
    const trialNo = t.trial_no || String(t.id || '');
    trialIdToNo[String(t.id || '')] = trialNo;
    const target = Number(t.target_enrollment || 0);
    const enrolled = trialEnrolledCounts[String(t.id || '')] || Number(t.enrolled_count || 0);
    
    // Calculate center count directly from DB extra_data
    let dbCenterCount = 0;
    if (t.extra_data && Array.isArray(t.extra_data.centers)) {
      dbCenterCount = t.extra_data.centers.length;
    }

    const calcCenterCount = trialCenterSets[String(t.id || '')] ? trialCenterSets[String(t.id || '')].size : 0;
    const centerCount = Math.max(dbCenterCount, calcCenterCount);

    
    // Calculate total budget from contracts later, but here we can just use the provided total_budget or 0
    return {
      id: trialNo,
      apiId: String(t.id || ''),
      name: t.full_name || t.short_name || trialNo,
      phase: t.phase || '-',
      status: mapTrialStatus(t.status),
      sponsor: t.sponsor || '-',
      indication: t.indication || '-',
      centerCount: centerCount,
      targetPatients: target,
      enrolled,
      startDate: t.planned_start || '-',
      pi: '-',
      progress: target > 0 ? Math.min(100, Math.round((enrolled / target) * 100)) : 0,
      budget: Number(t.total_budget || 0) / 10000,
      budgetUsed: Number(t.spent_amount || 0) / 10000,
      drugName: t.drug_name || '-',
      trial_code: t.trial_code || '',
      extra_data: t.extra_data || {} // Pass through extra_data for detail page
    };
  });

  // Need to process sites first to map site_id to site_name
  let siteRaw = [];
  if (sitesRes.status === 'fulfilled') {
    siteRaw = sitesRes.value.items || [];
  }
  
  CTMS_DATA.centerStats = siteRaw.map((s) => ({
    id: String(s.id),
    apiId: String(s.id),
    organizationId: s.organization_id || null,
    code: s.code || '-',
    center: s.name || '-',
    pi: s.pi_name || '-',
    phone: s.contact_phone || '-',
    email: s.contact_email || '-',
    address: s.address || '-',
    status: s.status || 'ACTIVE',
    enrolled: 0,
    target: 0,
    budget: 0,
    startupCycle: 0,
    budgetUsed: 0,
    qc: 0,
    sae: 0,
  }));

  const siteIdToName = {};
  CTMS_DATA.centerStats.forEach(c => {
    siteIdToName[c.apiId] = c.center;
  });

  CTMS_DATA.patients = patientsRaw.map((p) => {
    const patientNo = p.patient_no || String(p.id || '');
    patientIdToNo[String(p.id || '')] = patientNo;
    return {
      id: patientNo,
      apiId: String(p.id || ''),
      name: p.full_name || '受试者',
      age: Number(p.age || 0),
      gender: p.gender || '-',
      trialId: trialIdToNo[String(p.trial_id || '')] || String(p.trial_id || ''),
      screenDate: p.screening_date || null,
      enrollDate: p.enrollment_date || null,
      status: mapPatientStatus(p.status),
      visitCount: 0,
      nextVisit: null,
      icfSigned: p.consent_given === true || p.consent_given === 'true' || p.consent_given === 1,
      arm: p.arm || '-',
      center: siteIdToName[String(p.site_id || '')] || '-',
    };
  });

  const visitsRaw = visitsRes.status === 'fulfilled' ? (visitsRes.value.items || visitsRes.value.data || []) : [];
  CTMS_DATA.visits = visitsRaw.map((v) => ({
    id: String(v.id || ''),
    patientId: patientIdToNo[String(v.patient_id || '')] || String(v.patient_id || ''),
    visitName: v.visit_name || '-',
    planDate: v.planned_date || null,
    status: (v.status || ''),
    tasks: [],
  }));

  const patientVisitCount = {};
  const patientNextVisit = {};
  for (const v of CTMS_DATA.visits) {
    if (!v.patientId) continue;
    patientVisitCount[v.patientId] = (patientVisitCount[v.patientId] || 0) + 1;
    if (v.planDate && (!patientNextVisit[v.patientId] || v.planDate < patientNextVisit[v.patientId])) {
      patientNextVisit[v.patientId] = v.planDate;
    }
  }
  CTMS_DATA.patients = CTMS_DATA.patients.map((p) => ({
    ...p,
    visitCount: patientVisitCount[p.id] || 0,
    nextVisit: patientNextVisit[p.id] || null,
  }));

  const aeRaw = aeRes.status === 'fulfilled' ? (aeRes.value.items || aeRes.value.data || []) : [];
  CTMS_DATA.saeEvents = aeRaw
    .filter((a) => !!a.is_serious)
    .map((a) => ({
      id: String(a.ae_no || a.id || ''),
      trialId: trialIdToNo[String(a.trial_id || '')] || String(a.trial_id || ''),
      patientId: patientIdToNo[String(a.patient_id || '')] || String(a.patient_id || ''),
      eventName: a.description || '-',
      severity: a.severity || '-',
      reportDate: a.created_at || null,
      status: a.report_status || '-',
      causality: a.relatedness || '-',
      reportType: '首次报告',
    }));

  const drugsRaw = drugsRes.status === 'fulfilled' ? (drugsRes.value.items || []) : [];
  CTMS_DATA.drugs = drugsRaw.map((d) => ({
    id: String(d.id || ''),
    name: d.drug_name || '-',
    trialId: trialIdToNo[String(d.trial_id || '')] || String(d.trial_id || ''),
    batch: d.batch_no || '-',
    stock: Number(d.current_qty || 0),
    unit: d.unit || '-',
    expireDate: d.expiry_date || null,
    storeCond: d.storage_condition || '-',
    inDate: d.received_at || null,
    status: d.expiry_warning ? 'warning' : 'normal',
  }));

  const contractsRaw = contractsRes.status === 'fulfilled' ? (contractsRes.value.items || []) : [];
  CTMS_DATA.contracts = contractsRaw.map((c) => ({
    id: c.contract_no || String(c.id || ''),
    apiId: String(c.id || ''), // 补充保存后端真实主键 ID
    trialId: trialIdToNo[String(c.trial_id || '')] || String(c.trial_id || ''),
    type: c.contract_type || '-',
    sponsor: c.party_name || '-',
    amount: Number(c.total_amount || 0) / 10000, // 转换为万元展示
    signDate: c.sign_date || null,
    effectDate: c.start_date || null,
    status: (c.status || '').toLowerCase(),
    received: 0,
    invoiced: 0,
  }));

  // 拉取所有的付款计划/开票记录
  const paymentsRes = await API.finance.listPayments().catch(e => ({items:[]}));
  const paymentsRaw = paymentsRes.items || [];
  
  // 更新试验预算
  CTMS_DATA.trials.forEach(t => {
    const trialContracts = CTMS_DATA.contracts.filter(c => c.trialId === t.id);
    if (trialContracts.length > 0) {
      t.budget = trialContracts.reduce((sum, c) => sum + Number(c.amount || 0), 0);
    }
  });
  
  // 将 payment_type 为 "开票申请" 的记录提取到 invoices 列表中
  CTMS_DATA.invoices = paymentsRaw.filter(p => p.payment_type === "开票申请").map(p => {
    const c = CTMS_DATA.contracts.find(x => x.apiId === p.contract_id);
    // 从 description 中尝试提取出 title 和 taxId (格式 "抬头: XXX | 税号: XXX | 说明: XXX")
    let title = '科研经费', taxId = '-', notes = '';
    if (p.description) {
      const parts = p.description.split('|').map(s=>s.trim());
      parts.forEach(part => {
        if (part.startsWith('抬头:')) title = part.replace('抬头:', '').trim();
        else if (part.startsWith('税号:')) taxId = part.replace('税号:', '').trim();
        else if (part.startsWith('说明:')) notes = part.replace('说明:', '').trim();
      });
    }
    return {
      id: p.invoice_no || ('INV-' + String(p.id).substring(0,6).toUpperCase()),
      apiId: String(p.id),
      contractId: c ? c.id : (p.contract_id || '-'),
      contractTitle: c ? `${c.id} ${c.type}` : '-',
      amount: Number(p.planned_amount || 0),
      title: title,
      taxId: taxId,
      notes: notes,
      date: p.planned_date || p.created_at?.split('T')[0] || '-',
      status: p.status === 'PAID' ? '已开票' : '待开票'
    };
  });

  const notifRaw = notifRes.status === 'fulfilled' ? (notifRes.value.items || []) : [];
  CTMS_DATA.announcements = notifRaw.map((n) => ({
    id: String(n.id || ''),
    title: n.title || '-',
    time: n.created_at || '',
    type: (n.type || 'system').toLowerCase(),
    read: !!n.is_read,
  }));

  const trendRaw = trendRes.status === 'fulfilled' ? (trendRes.value.data || []) : [];
  CTMS_DATA.enrollTrend = trendRaw.map((r) => ({ month: r.period, count: Number(r.enrolled || 0) }));

  // 完全移除从 localStorage 恢复用户手动添加的中心数据，纯依赖后端
  // (Removed localCenters / ctms_deleted_center_codes fallback)

  const docsRaw = docsRes.status === 'fulfilled' ? (docsRes.value.items || []) : [];
  CTMS_DATA.documents = docsRaw.map(d => ({
    id: d.id,
    trialId: trialIdToNo[String(d.trial_id || '')] || String(d.trial_id || ''),
    title: d.title,
    docType: d.doc_type,
    centerName: d.site_name || d.center_name || (d.site && d.site.name) || '',
    fileName: d.file_name,
    fileSize: d.file_size,
    version: d.version,
    status: d.status,
    url: d.file_path || d.s3_url || d.s3_key,
    createdAt: d.created_at
  }));

  const iwrsSchemesRaw = iwrsSchemesRes.status === 'fulfilled' ? (iwrsSchemesRes.value.items || iwrsSchemesRes.value || []) : [];
  CTMS_DATA.iwrsSchemes = iwrsSchemesRaw.map(s => ({
    id: s.id,
    scheme_code: s.scheme_code,
    name: s.scheme_name,
    type: s.scheme_type === 'SIMPLE' ? '简单随机' : (s.scheme_type === 'BLOCK' ? '区组随机' : '分层随机'),
    strata: s.strata_factors || [],
    blockSize: (s.block_sizes || []).join(','),
    ratio: s.ratio,
    total: s.total_subjects,
    used: 0, // will be updated below or needs separate stat call
    status: s.status === 'ACTIVE' ? '进行中' : (s.status === 'COMPLETED' ? '已完成' : (s.status === 'DRAFT' ? '草稿' : '已暂停')),
    trialId: trialIdToNo[String(s.trial_id || '')] || String(s.trial_id || '')
  }));

  const iwrsSubjectsRaw = iwrsSubjectsRes.status === 'fulfilled' ? (iwrsSubjectsRes.value || []) : [];
  CTMS_DATA.iwrsSubjects = iwrsSubjectsRaw.map(r => ({
    id: r.id,
    subjectId: r.subject_code,
    patientId: patientIdToNo[String(r.patient_id || '')] || String(r.patient_id || ''),
    schemeId: r.scheme_id,
    randomCode: r.randomization_code,
    treatment: r.treatment_name || r.treatment_arm || '',
    treatmentName: r.treatment_name || '',
    treatmentArm: r.treatment_arm || '',
    date: CTMS.formatDateTime(r.assigned_at),
    status: r.is_blinded ? '盲态' : '已解盲'
  }));

  // Update used count
  for (const s of CTMS_DATA.iwrsSchemes) {
    s.used = CTMS_DATA.iwrsSubjects.filter(sub => sub.schemeId === s.id).length;
  }

  const drugLogsRaw = drugLogsRes.status === 'fulfilled' ? (drugLogsRes.value || []) : [];
  
  // 建立可访问的权限集合
  const validDrugIds = new Set(CTMS_DATA.drugs.map(d => String(d.id)));
  const validDrugBatches = new Set(CTMS_DATA.drugs.map(d => d.batch));
  const validPatientApiIds = new Set(CTMS_DATA.patients.map(p => String(p.apiId)));

  // 1. 先过滤出有权限的发药和入库记录
  let filteredLogs = drugLogsRaw.filter(l => {
    if (l.type === 'inbound') {
      return validDrugBatches.has(l.drugId) || CTMS_DATA.drugs.some(d => d.name === l.drugId);
    } else if (l.type === 'dispatch') {
      return validPatientApiIds.has(String(l.patientId)) || validDrugIds.has(String(l.drugId));
    }
    return true; // 暂放行return，第二轮过滤
  });

  // 2. 建立有效发药记录ID集合
  const validDispatchIds = new Set(filteredLogs.filter(l => l.type === 'dispatch').map(l => String(l.id)));

  // 3. 过滤回收记录 (drugId 存的是 dispense_id)
  CTMS_DATA.drugLogs = filteredLogs.filter(l => {
    if (l.type === 'return') {
      return validDispatchIds.has(String(l.drugId));
    }
    return true;
  }).map(l => ({
    ...l,
    patientId: patientIdToNo[String(l.patientId || '')] || String(l.patientId || '')
  }));

  const usersRaw = usersRes.status === 'fulfilled' ? (usersRes.value.items || []) : [];
  CTMS_DATA.users = usersRaw.map(u => {
    // Determine center name from organization_id if it matches a site
    let centerName = '外部'; // Default
    if (u.organization_id) {
       const matchedSite = siteRaw.find(s => String(s.organization_id) === String(u.organization_id));
       if (matchedSite) centerName = matchedSite.name;
    }
    
    return {
      id: String(u.id),
      apiId: String(u.id),
      name: u.full_name || u.username,
      email: u.email,
      phone: u.phone || '',
      role: u.role_name || u.title || '-',
      dept: u.department || '-',
      center: centerName,
      status: u.is_active ? 'active' : 'inactive',
      last: CTMS.formatDateTime(u.last_login_at)
    };
  });

  // 获取并保存系统角色列表
  const rolesRaw = rolesRes2 && rolesRes2.status === 'fulfilled' ? (rolesRes2.value.data || rolesRes2.value.items || []) : [];
  if (rolesRaw.length > 0) {
      CTMS_DATA.roles = rolesRaw.map(r => ({
          id: r.id,
          code: r.code,
          name: r.name
      }));
  }

  const timesheetsRaw = timesheetsRes.status === 'fulfilled' ? (timesheetsRes.value.items || []) : [];
  CTMS_DATA.timesheets = timesheetsRaw.map(t => ({
    id: String(t.id),
    apiId: String(t.id),
    date: t.date,
    project: t.project,
    task: t.task,
    hours: t.hours,
    notes: t.notes,
    user_name: t.user_name || ''
  }));

  CTMS_DATA.milestones = [];
  CTMS_DATA.auditLogs = [];
  CTMS_DATA.qcRecords = [];

  return true;
}

window.syncCTMSDataFromPostgreSQL = syncCTMSDataFromPostgreSQL;
=======
// CTMS 系统模拟数据 (Mock data cleared, relying purely on PostgreSQL)
const CTMS_DATA = {
  currentUser: { name: '用户', role: '-', dept: '-', avatar: 'U' },
  
  trials: [],
  patients: [],
  drugs: [],
  drugLogs: [],
  contracts: [],
  milestones: [],
  saeEvents: [],
  visits: [],
  auditLogs: [],
  qcRecords: [],
  announcements: [],
  centerStats: [],
  enrollTrend: [],
  documents: [],
  users: [],
  timesheets: []
};

// 辅助函数
function getTrialById(id) { return CTMS_DATA.trials.find(t => t.id === id); }
function getPatientsByTrial(trialId) { return CTMS_DATA.patients.filter(p => p.trialId === trialId); }
function getStatusLabel(status) {
  const map = { running: '进行中', startup: '启动期', closing: '结题中', done: '已完成', pending: '待完成', screen_fail: '筛选失败', enrolled: '已入组', screening: '筛选中', dropout: '脱落', active: '生效中', normal: '正常', warning: '近效期' };
  return map[status] || status;
}
function getStatusBadge(status) {
  const map = { running: 'badge-green', startup: 'badge-blue', closing: 'badge-yellow', done: 'badge-gray', pending: 'badge-yellow', screen_fail: 'badge-red', enrolled: 'badge-green', screening: 'badge-blue', dropout: 'badge-gray', active: 'badge-green', normal: 'badge-green', warning: 'badge-yellow' };
  return map[status] || 'badge-gray';
}
function formatDate(d) { if (!d) return '-'; return d; }
function calcDays(d1, d2) { if (!d1 || !d2) return 0; return Math.round((new Date(d2) - new Date(d1)) / 86400000); }

function mapTrialStatus(status) {
  const m = {
    ONGOING: 'running',
    RECRUITING: 'running',
    PLANNING: 'startup',
    INITIATING: 'startup',
    COMPLETED: 'done',
    TERMINATED: 'closing',
    SUSPENDED: 'closing',
  };
  return m[status] || 'running';
}

function mapPatientStatus(status) {
  const m = {
    ENROLLED: 'enrolled',
    SCREENING: 'screening',
    SCREEN_FAIL: 'screen_fail',
    SCREEN_FAILED: 'screen_fail',
    WITHDRAWN: 'dropout',
    COMPLETED: 'done',
    ACTIVE: 'enrolled',
  };
  return m[status] || 'screening';
}

async function syncCTMSDataFromPostgreSQL() {
  if (!window.CTMS_API || !CTMS_API.Token.getAccessToken()) return false;

  const results = await Promise.allSettled([
      CTMS_API.Trial.list({ page: 1, page_size: 100 }),
      CTMS_API.Patient.list({ page: 1, page_size: 100 }),
      CTMS_API.Visit.list({ page: 1, page_size: 500 }),
      CTMS_API.AE.list({}),
      CTMS_API.Drug.listBatches({}),
      CTMS_API.Finance.listContracts({}),
      CTMS_API.Notification.list({ page: 1, page_size: 50 }),
      CTMS_API.Report.enrollmentTrend({ months: 12 }),
      window.API.sites.list({ page: 1, page_size: 500 }),
      CTMS_API.Document.list({ page: 1, page_size: 500 }),
      CTMS_API.IWRS.listSchemes({ page: 1, page_size: 100 }),
      CTMS_API.IWRS.listRandomizations({ page: 1, page_size: 100 }),
      window.API.drugs.listLogs({ limit: 50 }),
      window.API.users.list({ page: 1, page_size: 100 }),
      window.API.timesheets.list({ page: 1, page_size: 500 }),
      fetch(window.API_BASE_URL + '/roles', { headers: { 'Authorization': 'Bearer ' + localStorage.getItem('access_token') } }).then(r => r.json())
    ]);

  const [trialsRes, patientsRes, visitsRes, aeRes, drugsRes, contractsRes, notifRes, trendRes, sitesRes, docsRes, iwrsSchemesRes, iwrsSubjectsRes, drugLogsRes, usersRes, timesheetsRes, rolesRes2] = results;

  const trialsRaw = trialsRes.status === 'fulfilled' ? (trialsRes.value.items || []) : [];
  const trialIdToNo = {};
  
  const patientsRaw = patientsRes.status === 'fulfilled' ? (patientsRes.value.items || []) : [];
  const patientIdToNo = {};
  
  // Calculate real enrolled count and center count per trial from patients list
  const trialEnrolledCounts = {};
  const trialCenterSets = {};
  patientsRaw.forEach(p => {
    const tId = String(p.trial_id || '');
    if (mapPatientStatus(p.status) === 'enrolled') {
      trialEnrolledCounts[tId] = (trialEnrolledCounts[tId] || 0) + 1;
    }
    if (p.site_id) {
      if (!trialCenterSets[tId]) trialCenterSets[tId] = new Set();
      trialCenterSets[tId].add(p.site_id);
    }
  });

  CTMS_DATA.trials = trialsRaw.map((t) => {
    const trialNo = t.trial_no || String(t.id || '');
    trialIdToNo[String(t.id || '')] = trialNo;
    const target = Number(t.target_enrollment || 0);
    const enrolled = trialEnrolledCounts[String(t.id || '')] || Number(t.enrolled_count || 0);
    const centerCount = trialCenterSets[String(t.id || '')] ? trialCenterSets[String(t.id || '')].size : 0;
    
    // Calculate total budget from contracts later, but here we can just use the provided total_budget or 0
    return {
      id: trialNo,
      apiId: String(t.id || ''),
      name: t.full_name || t.short_name || trialNo,
      phase: t.phase || '-',
      status: mapTrialStatus(t.status),
      sponsor: t.sponsor || '-',
      indication: t.indication || '-',
      centerCount: centerCount,
      targetPatients: target,
      enrolled,
      startDate: t.planned_start || '-',
      pi: '-',
      progress: target > 0 ? Math.min(100, Math.round((enrolled / target) * 100)) : 0,
      budget: Number(t.total_budget || 0) / 10000,
      budgetUsed: Number(t.spent_amount || 0) / 10000,
      drugName: t.drug_name || '-',
    };
  });

  // Need to process sites first to map site_id to site_name
  let siteRaw = [];
  if (sitesRes.status === 'fulfilled') {
    siteRaw = sitesRes.value.items || [];
  }
  
  CTMS_DATA.centerStats = siteRaw.map((s) => ({
    id: String(s.id),
    apiId: String(s.id),
    organizationId: s.organization_id || null,
    code: s.code || '-',
    center: s.name || '-',
    pi: s.pi_name || '-',
    phone: s.contact_phone || '-',
    email: s.contact_email || '-',
    address: s.address || '-',
    status: s.status || 'ACTIVE',
    enrolled: 0,
    target: 0,
    budget: 0,
    startupCycle: 0,
    budgetUsed: 0,
    qc: 0,
    sae: 0,
  }));

  const siteIdToName = {};
  CTMS_DATA.centerStats.forEach(c => {
    siteIdToName[c.apiId] = c.center;
  });

  CTMS_DATA.patients = patientsRaw.map((p) => {
    const patientNo = p.patient_no || String(p.id || '');
    patientIdToNo[String(p.id || '')] = patientNo;
    return {
      id: patientNo,
      apiId: String(p.id || ''),
      name: p.full_name || '受试者',
      age: Number(p.age || 0),
      gender: p.gender || '-',
      trialId: trialIdToNo[String(p.trial_id || '')] || String(p.trial_id || ''),
      screenDate: p.screening_date || null,
      enrollDate: p.enrollment_date || null,
      status: mapPatientStatus(p.status),
      visitCount: 0,
      nextVisit: null,
      icfSigned: p.consent_given === true || p.consent_given === 'true' || p.consent_given === 1,
      arm: p.arm || '-',
      center: siteIdToName[String(p.site_id || '')] || '-',
    };
  });

  const visitsRaw = visitsRes.status === 'fulfilled' ? (visitsRes.value.items || visitsRes.value.data || []) : [];
  CTMS_DATA.visits = visitsRaw.map((v) => ({
    id: String(v.id || ''),
    patientId: patientIdToNo[String(v.patient_id || '')] || String(v.patient_id || ''),
    visitName: v.visit_name || '-',
    planDate: v.planned_date || null,
    status: (v.status || ''),
    tasks: [],
  }));

  const patientVisitCount = {};
  const patientNextVisit = {};
  for (const v of CTMS_DATA.visits) {
    if (!v.patientId) continue;
    patientVisitCount[v.patientId] = (patientVisitCount[v.patientId] || 0) + 1;
    if (v.planDate && (!patientNextVisit[v.patientId] || v.planDate < patientNextVisit[v.patientId])) {
      patientNextVisit[v.patientId] = v.planDate;
    }
  }
  CTMS_DATA.patients = CTMS_DATA.patients.map((p) => ({
    ...p,
    visitCount: patientVisitCount[p.id] || 0,
    nextVisit: patientNextVisit[p.id] || null,
  }));

  const aeRaw = aeRes.status === 'fulfilled' ? (aeRes.value.items || aeRes.value.data || []) : [];
  CTMS_DATA.saeEvents = aeRaw
    .filter((a) => !!a.is_serious)
    .map((a) => ({
      id: String(a.ae_no || a.id || ''),
      trialId: trialIdToNo[String(a.trial_id || '')] || String(a.trial_id || ''),
      patientId: patientIdToNo[String(a.patient_id || '')] || String(a.patient_id || ''),
      eventName: a.description || '-',
      severity: a.severity || '-',
      reportDate: a.created_at || null,
      status: a.report_status || '-',
      causality: a.relatedness || '-',
      reportType: '首次报告',
    }));

  const drugsRaw = drugsRes.status === 'fulfilled' ? (drugsRes.value.items || []) : [];
  CTMS_DATA.drugs = drugsRaw.map((d) => ({
    id: String(d.id || ''),
    name: d.drug_name || '-',
    trialId: trialIdToNo[String(d.trial_id || '')] || String(d.trial_id || ''),
    batch: d.batch_no || '-',
    stock: Number(d.current_qty || 0),
    unit: d.unit || '-',
    expireDate: d.expiry_date || null,
    storeCond: d.storage_condition || '-',
    inDate: d.received_at || null,
    status: d.expiry_warning ? 'warning' : 'normal',
  }));

  const contractsRaw = contractsRes.status === 'fulfilled' ? (contractsRes.value.items || []) : [];
  CTMS_DATA.contracts = contractsRaw.map((c) => ({
    id: c.contract_no || String(c.id || ''),
    apiId: String(c.id || ''), // 补充保存后端真实主键 ID
    trialId: trialIdToNo[String(c.trial_id || '')] || String(c.trial_id || ''),
    type: c.contract_type || '-',
    sponsor: c.party_name || '-',
    amount: Number(c.total_amount || 0) / 10000, // 转换为万元展示
    signDate: c.sign_date || null,
    effectDate: c.start_date || null,
    status: (c.status || '').toLowerCase(),
    received: 0,
    invoiced: 0,
  }));

  // 拉取所有的付款计划/开票记录
  const paymentsRes = await API.finance.listPayments().catch(e => ({items:[]}));
  const paymentsRaw = paymentsRes.items || [];
  
  // 更新试验预算
  CTMS_DATA.trials.forEach(t => {
    const trialContracts = CTMS_DATA.contracts.filter(c => c.trialId === t.id);
    if (trialContracts.length > 0) {
      t.budget = trialContracts.reduce((sum, c) => sum + Number(c.amount || 0), 0);
    }
  });
  
  // 将 payment_type 为 "开票申请" 的记录提取到 invoices 列表中
  CTMS_DATA.invoices = paymentsRaw.filter(p => p.payment_type === "开票申请").map(p => {
    const c = CTMS_DATA.contracts.find(x => x.apiId === p.contract_id);
    // 从 description 中尝试提取出 title 和 taxId (格式 "抬头: XXX | 税号: XXX | 说明: XXX")
    let title = '科研经费', taxId = '-', notes = '';
    if (p.description) {
      const parts = p.description.split('|').map(s=>s.trim());
      parts.forEach(part => {
        if (part.startsWith('抬头:')) title = part.replace('抬头:', '').trim();
        else if (part.startsWith('税号:')) taxId = part.replace('税号:', '').trim();
        else if (part.startsWith('说明:')) notes = part.replace('说明:', '').trim();
      });
    }
    return {
      id: p.invoice_no || ('INV-' + String(p.id).substring(0,6).toUpperCase()),
      apiId: String(p.id),
      contractId: c ? c.id : (p.contract_id || '-'),
      contractTitle: c ? `${c.id} ${c.type}` : '-',
      amount: Number(p.planned_amount || 0),
      title: title,
      taxId: taxId,
      notes: notes,
      date: p.planned_date || p.created_at?.split('T')[0] || '-',
      status: p.status === 'PAID' ? '已开票' : '待开票'
    };
  });

  const notifRaw = notifRes.status === 'fulfilled' ? (notifRes.value.items || []) : [];
  CTMS_DATA.announcements = notifRaw.map((n) => ({
    id: String(n.id || ''),
    title: n.title || '-',
    time: n.created_at || '',
    type: (n.type || 'system').toLowerCase(),
    read: !!n.is_read,
  }));

  const trendRaw = trendRes.status === 'fulfilled' ? (trendRes.value.data || []) : [];
  CTMS_DATA.enrollTrend = trendRaw.map((r) => ({ month: r.period, count: Number(r.enrolled || 0) }));

  // 完全移除从 localStorage 恢复用户手动添加的中心数据，纯依赖后端
  // (Removed localCenters / ctms_deleted_center_codes fallback)

  const docsRaw = docsRes.status === 'fulfilled' ? (docsRes.value.items || []) : [];
  CTMS_DATA.documents = docsRaw.map(d => ({
    id: d.id,
    trialId: trialIdToNo[String(d.trial_id || '')] || String(d.trial_id || ''),
    title: d.title,
    docType: d.doc_type,
    centerName: d.site_name || d.center_name || (d.site && d.site.name) || '',
    fileName: d.file_name,
    fileSize: d.file_size,
    version: d.version,
    status: d.status,
    url: d.file_path || d.s3_url || d.s3_key,
    createdAt: d.created_at
  }));

  const iwrsSchemesRaw = iwrsSchemesRes.status === 'fulfilled' ? (iwrsSchemesRes.value.items || iwrsSchemesRes.value || []) : [];
  CTMS_DATA.iwrsSchemes = iwrsSchemesRaw.map(s => ({
    id: s.id,
    scheme_code: s.scheme_code,
    name: s.scheme_name,
    type: s.scheme_type === 'SIMPLE' ? '简单随机' : (s.scheme_type === 'BLOCK' ? '区组随机' : '分层随机'),
    strata: s.strata_factors || [],
    blockSize: (s.block_sizes || []).join(','),
    ratio: s.ratio,
    total: s.total_subjects,
    used: 0, // will be updated below or needs separate stat call
    status: s.status === 'ACTIVE' ? '进行中' : (s.status === 'COMPLETED' ? '已完成' : (s.status === 'DRAFT' ? '草稿' : '已暂停')),
    trialId: trialIdToNo[String(s.trial_id || '')] || String(s.trial_id || '')
  }));

  const iwrsSubjectsRaw = iwrsSubjectsRes.status === 'fulfilled' ? (iwrsSubjectsRes.value || []) : [];
  CTMS_DATA.iwrsSubjects = iwrsSubjectsRaw.map(r => ({
    id: r.id,
    subjectId: r.subject_code,
    patientId: patientIdToNo[String(r.patient_id || '')] || String(r.patient_id || ''),
    schemeId: r.scheme_id,
    randomCode: r.randomization_code,
    treatment: r.treatment_name || r.treatment_arm || '',
    treatmentName: r.treatment_name || '',
    treatmentArm: r.treatment_arm || '',
    date: CTMS.formatDateTime(r.assigned_at),
    status: r.is_blinded ? '盲态' : '已解盲'
  }));

  // Update used count
  for (const s of CTMS_DATA.iwrsSchemes) {
    s.used = CTMS_DATA.iwrsSubjects.filter(sub => sub.schemeId === s.id).length;
  }

  const drugLogsRaw = drugLogsRes.status === 'fulfilled' ? (drugLogsRes.value || []) : [];
  
  // 建立可访问的权限集合
  const validDrugIds = new Set(CTMS_DATA.drugs.map(d => String(d.id)));
  const validDrugBatches = new Set(CTMS_DATA.drugs.map(d => d.batch));
  const validPatientApiIds = new Set(CTMS_DATA.patients.map(p => String(p.apiId)));

  // 1. 先过滤出有权限的发药和入库记录
  let filteredLogs = drugLogsRaw.filter(l => {
    if (l.type === 'inbound') {
      return validDrugBatches.has(l.drugId) || CTMS_DATA.drugs.some(d => d.name === l.drugId);
    } else if (l.type === 'dispatch') {
      return validPatientApiIds.has(String(l.patientId)) || validDrugIds.has(String(l.drugId));
    }
    return true; // 暂放行return，第二轮过滤
  });

  // 2. 建立有效发药记录ID集合
  const validDispatchIds = new Set(filteredLogs.filter(l => l.type === 'dispatch').map(l => String(l.id)));

  // 3. 过滤回收记录 (drugId 存的是 dispense_id)
  CTMS_DATA.drugLogs = filteredLogs.filter(l => {
    if (l.type === 'return') {
      return validDispatchIds.has(String(l.drugId));
    }
    return true;
  }).map(l => ({
    ...l,
    patientId: patientIdToNo[String(l.patientId || '')] || String(l.patientId || '')
  }));

  const usersRaw = usersRes.status === 'fulfilled' ? (usersRes.value.items || []) : [];
  CTMS_DATA.users = usersRaw.map(u => {
    // Determine center name from organization_id if it matches a site
    let centerName = '外部'; // Default
    if (u.organization_id) {
       const matchedSite = siteRaw.find(s => String(s.organization_id) === String(u.organization_id));
       if (matchedSite) centerName = matchedSite.name;
    }
    
    return {
      id: String(u.id),
      apiId: String(u.id),
      name: u.full_name || u.username,
      email: u.email,
      role: u.role_name || u.title || '-',
      dept: u.department || '-',
      center: centerName,
      status: u.is_active ? 'active' : 'inactive',
      last: CTMS.formatDateTime(u.last_login_at)
    };
  });

  // 获取并保存系统角色列表
  const rolesRaw = rolesRes2 && rolesRes2.status === 'fulfilled' ? (rolesRes2.value.data || rolesRes2.value.items || []) : [];
  if (rolesRaw.length > 0) {
      CTMS_DATA.roles = rolesRaw.map(r => ({
          id: r.id,
          code: r.code,
          name: r.name
      }));
  }

  const timesheetsRaw = timesheetsRes.status === 'fulfilled' ? (timesheetsRes.value.items || []) : [];
  CTMS_DATA.timesheets = timesheetsRaw.map(t => ({
    id: String(t.id),
    apiId: String(t.id),
    date: t.date,
    project: t.project,
    task: t.task,
    hours: t.hours,
    notes: t.notes,
    user_name: t.user_name || ''
  }));

  CTMS_DATA.milestones = [];
  CTMS_DATA.auditLogs = [];
  CTMS_DATA.qcRecords = [];

  return true;
}

window.syncCTMSDataFromPostgreSQL = syncCTMSDataFromPostgreSQL;
>>>>>>> origin/main
