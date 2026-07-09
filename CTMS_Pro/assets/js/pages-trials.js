// 各页面渲染函数
const PAGES = {};

// ===== 数据概览 =====
PAGES.dashboard = async function() {
  const totalEnrolled = CTMS_DATA.trials.reduce((s,t)=>s+t.enrolled,0);
  const totalTarget = CTMS_DATA.trials.reduce((s,t)=>s+t.targetPatients,0);
  const runningTrials = CTMS_DATA.trials.filter(t=>t.status==='running').length;
  
  document.getElementById('main-content').innerHTML = '<div class="page-section">加载中...</div>';

  let notifs = [];
  if (window.API) {
    try {
      const notifRes = await window.API.notifications.list({page: 1, page_size: 5});
      notifs = notifRes.items || [];
    } catch(e) {
      console.error(e);
    }
  }

  document.getElementById('main-content').innerHTML = `
    <div class="page-section">
      <div class="flex-between mb-16">
        <div>
          <div class="page-title">数据概览</div>
          <div class="page-subtitle">欢迎回来，${CTMS_DATA.currentUser.name} · ${new Date().toLocaleDateString('zh-CN', {year:'numeric',month:'long',day:'numeric',weekday:'long'})}</div>
        </div>
        <button class="btn btn-primary" onclick="CTMS.navigate('trials')">📋 查看所有试验</button>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon blue">🔬</div>
          <div class="stat-info">
            <div class="stat-value">${CTMS_DATA.trials.length}</div>
            <div class="stat-label">试验项目总数</div>
            <div class="stat-change up">▲ ${runningTrials} 项进行中</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">👥</div>
          <div class="stat-info">
            <div class="stat-value">${totalEnrolled}</div>
            <div class="stat-label">已入组受试者</div>
            <div class="stat-change up">总目标 ${totalTarget} 人（${Math.round(totalEnrolled/totalTarget*100)}%）</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon yellow">⚠️</div>
          <div class="stat-info">
            <div class="stat-value">${CTMS_DATA.saeEvents.length}</div>
            <div class="stat-label">SAE报告</div>
            <div class="stat-change down">▼ ${CTMS_DATA.saeEvents.filter(s=>s.status==='FOLLOW_UP' || s.status==='随访中').length} 项随访中</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon red">💊</div>
          <div class="stat-info">
            <div class="stat-value">${CTMS_DATA.drugs.filter(d=>d.status==='warning').length}</div>
            <div class="stat-label">药品近效期预警</div>
            <div class="stat-change down">需尽快处置</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon purple">📅</div>
          <div class="stat-info">
            <div class="stat-value">${CTMS_DATA.visits.filter(v=>v.status==='SCHEDULED' || v.status==='pending').length}</div>
            <div class="stat-label">待完成访视</div>
            <div class="stat-change">近7天内需完成</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon cyan">✅</div>
          <div class="stat-info">
            <div class="stat-value">${CTMS_DATA.documents.length > 0 ? Math.round(CTMS_DATA.documents.filter(d=>d.status==='APPROVED').length / CTMS_DATA.documents.length * 100) : 100}%</div>
            <div class="stat-label">合规通过率</div>
            <div class="stat-change up">▲ eTMF文档数 ${CTMS_DATA.documents.length} 份</div>
          </div>
        </div>
      </div>

      <div class="grid2">
        <!-- 试验入组进度 -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">📊 试验入组进度</div>
            <button class="btn btn-sm btn-secondary" onclick="CTMS.navigate('trials')">查看全部</button>
          </div>
          <div class="card-body">
            ${CTMS_DATA.trials.map(t=>`
              <div style="margin-bottom:14px">
                <div class="flex-between mb-4">
                  <span style="font-size:13px;font-weight:500;cursor:pointer;color:var(--primary)" onclick="CTMS.navigate('trial-detail',{trialId:'${t.id}',trialApiId:'${t.apiId || ''}'})">${t.id}: ${t.name.substring(0,16)}...</span>
                  <span class="badge ${getStatusBadge(t.status)}">${getStatusLabel(t.status)}</span>
                </div>
                <div class="flex-between" style="font-size:12px;color:var(--gray-500);margin-bottom:4px">
                  <span>${t.indication}</span>
                  <span>${t.enrolled || 0}/${t.targetPatients || 0} 人 · ${t.progress || 0}%</span>
                </div>
                <div class="progress-bar"><div class="progress-fill ${t.progress>=80?'green':t.progress>=50?'blue':'yellow'}" style="width:${t.progress}%"></div></div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- 入组趋势 -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">📈 ${CTMS_DATA.trials && CTMS_DATA.trials.length > 0 ? CTMS_DATA.trials[0].id : '未知试验'} 入组趋势</div>
          </div>
          <div class="card-body">
            <canvas id="enrollChart" width="400" height="180"></canvas>
          </div>
        </div>
      </div>
    </div>
  `;
  drawCharts();
};

function drawCharts() {
  // 入组趋势折线图
  const enrollCtx = document.getElementById('enrollChart');
  if (enrollCtx && window.Chart) {
    const d = CTMS_DATA.enrollTrend;
    new Chart(enrollCtx, {
      type: 'line',
      data: {
        labels: d.map(x=>x.month.substring(5)),
        datasets: [{
          label: '当月入组人数',
          data: d.map(x=>x.count),
          borderColor: '#1a6fc4',
          backgroundColor: 'rgba(26,111,196,0.08)',
          tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: '#1a6fc4'
        },{
          label: '累计入组',
          data: d.reduce((acc,x,i)=>[...acc,(acc[i-1]||0)+x.count],[]),
          borderColor: '#22c55e',
          backgroundColor: 'rgba(34,197,94,0.05)',
          tension: 0.4, fill: false, pointRadius: 4, pointBackgroundColor: '#22c55e'
        }]
      },
      options: { responsive: true, plugins: { legend: { position: 'top', labels:{font:{size:11}} } }, scales: { y: { beginAtZero: true, grid:{color:'rgba(0,0,0,0.05)'} }, x:{grid:{display:false}} } }
    });
  }

  // 中心对比柱状图
  const centerCtx = document.getElementById('centerChart');
  if (centerCtx && window.Chart) {
    const cs = CTMS_DATA.centerStats;
    new Chart(centerCtx, {
      type: 'bar',
      data: {
        labels: cs.map(c=>c.center.replace('医院','').replace('大学附属','').replace('大学','').substring(0,6)),
        datasets: [
          { label: '已入组', data: cs.map(c=>c.enrolled), backgroundColor: '#1a6fc4', borderRadius: 4 },
          { label: '目标', data: cs.map(c=>c.target), backgroundColor: '#e5e7eb', borderRadius: 4 }
        ]
      },
      options: { responsive: true, plugins: { legend: { position:'top', labels:{font:{size:11}} } }, scales: { x:{grid:{display:false}}, y:{beginAtZero:true,grid:{color:'rgba(0,0,0,0.05)'}} } }
    });
  }
}

// ===== 我的试验列表 =====
PAGES.trials = function() {
  document.getElementById('main-content').innerHTML = `
    <div class="page-section">
      <div class="flex-between mb-16">
        <div><div class="page-title">我的试验</div><div class="page-subtitle">管理所有临床试验项目</div></div>
        <button class="btn btn-primary" onclick="CTMS.showNewTrialModal()">＋ 新建试验</button>
      </div>
      <div class="search-bar">
        <div class="search-input-wrap">
          <span class="search-icon">🔍</span>
          <input type="text" placeholder="搜索试验编号、名称、申办方..." id="trial-search">
        </div>
        <select onchange="filterTrials(this.value)" style="padding:7px 12px;border:1px solid var(--gray-300);border-radius:6px;font-size:13px">
          <option value="">全部状态</option>
          <option value="running">进行中</option>
          <option value="startup">启动期</option>
          <option value="closing">结题中</option>
        </select>
        <select style="padding:7px 12px;border:1px solid var(--gray-300);border-radius:6px;font-size:13px">
          <option value="">全部阶段</option>
          <option value="8">I期</option><option value="9">II期</option><option value="10">III期</option><option value="11">IV期</option><option value="12">上市后临床研究</option>
          <option value="1">药物临床试验</option><option value="2">中保研究</option><option value="3">医疗器械临床试验</option>
          <option value="4">科研项目其他</option><option value="5">药物上市后再评价</option><option value="6">医疗器械上市后再评价</option><option value="7">其他</option>
        </select>
      </div>
      <div id="trials-grid" class="grid2" style="grid-template-columns:1fr 1fr 1fr"></div>
    </div>
  `;
  loadTrialsFromAPI();
  document.getElementById('trial-search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    renderTrialCards(CTMS_DATA.trials.filter(t=>t.name.includes(q)||t.id.toLowerCase().includes(q)||t.sponsor.includes(q)));
  });
};

function mapTrialStatusFromApi(status) {
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

function mapApiTrialToCard(t) {
  const target = Number(t.target_enrollment || 0);
  
  // Calculate center count directly from DB extra_data
  let dbCenterCount = 0;
  if (t.extra_data && Array.isArray(t.extra_data.centers)) {
    dbCenterCount = t.extra_data.centers.length;
  }
  
  // Calculate real enrolled count and center count per trial from patients list
  let realEnrolled = 0;
  let calculatedCenterCount = 0;
  if (CTMS_DATA.patients && CTMS_DATA.patients.length > 0) {
    const matchedPatients = CTMS_DATA.patients.filter(p => p.trialId === (t.trial_no || String(t.id || '')) || p.trialId === String(t.id || ''));
    realEnrolled = matchedPatients.filter(p => p.status === 'enrolled').length;
    const centers = new Set();
    matchedPatients.forEach(p => {
      if (p.center && p.center !== '-') centers.add(p.center);
    });
    calculatedCenterCount = centers.size;
  }
  const enrolled = realEnrolled || Number(t.enrolled_count || 0);

  // Calculate budget from contracts
  let calculatedBudget = Number(t.total_budget || 0) / 10000;
  if (CTMS_DATA.contracts && CTMS_DATA.contracts.length > 0) {
    const matchedContracts = CTMS_DATA.contracts.filter(c => c.trialId === (t.trial_no || String(t.id || '')) || c.trialId === String(t.id || ''));
    if (matchedContracts.length > 0) {
      calculatedBudget = matchedContracts.reduce((sum, c) => sum + Number(c.amount || 0), 0);
    }
  }
  
  return {
    id: t.trial_no || String(t.id || ''),
    apiId: String(t.id || ''),
    name: t.full_name || t.short_name || '-',
    phase: t.phase || '-',
    status: mapTrialStatusFromApi(t.status),
    sponsor: t.sponsor || '-',
    indication: t.indication || '-',
    centerCount: Math.max(dbCenterCount, calculatedCenterCount, t.centerCount || 0),
    targetPatients: target,
    enrolled,
    startDate: t.planned_start || '-',
    pi: '-',
    progress: target > 0 ? Math.min(100, Math.round((enrolled / target) * 100)) : 0,
    budget: calculatedBudget,
    budgetUsed: Number(t.spent_amount || 0) / 10000,
    drugName: t.drug_name || '-',
    trial_code: t.trial_code || '',
    extra_data: t.extra_data || {} // Pass through extra_data so detail page can use it
  };
}

async function loadTrialsFromAPI() {
  try {
    const res = await API.trials.list({ page: 1, page_size: 100 });
    const items = (res && res.items) ? res.items : [];
    CTMS_DATA.trials = items.map(mapApiTrialToCard);
    renderTrialCards(CTMS_DATA.trials);
  } catch (e) {
    CTMS.showToast(e.message || '试验列表加载失败', 'error');
    renderTrialCards(CTMS_DATA.trials);
  }
}

function renderTrialCards(trials) {
  document.getElementById('trials-grid').innerHTML = trials.map(t => `
    <div class="card" style="cursor:pointer;transition:var(--transition)" onmouseover="this.style.boxShadow='var(--shadow)'" onmouseout="this.style.boxShadow=''" onclick="CTMS.navigate('trial-detail',{trialId:'${t.id}',trialApiId:'${t.apiId || ''}'})">
      <div class="card-body">
        <div class="flex-between mb-8">
          <span class="badge badge-blue" style="font-size:11px">${CTMS.getPhaseName(t.phase)}</span>
          <span class="badge ${getStatusBadge(t.status)}">${getStatusLabel(t.status)}</span>
        </div>
        <div class="flex-between mb-8">
          <div></div>
          <div style="display:flex;gap:6px">
            <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();CTMS.completeTrial('${t.apiId || ''}','${t.id}')" ${t.status === 'done' ? 'disabled' : ''}>✅ 完成</button>
            <button class="btn btn-sm btn-danger" onclick="event.stopPropagation();CTMS.deleteTrial('${t.apiId || ''}','${t.id}')">🗑️ 删除</button>
          </div>
        </div>
        <div style="font-size:14px;font-weight:600;color:var(--gray-900);margin-bottom:6px;line-height:1.4">${t.name}</div>
        <div style="font-size:12px;color:var(--gray-500);margin-bottom:10px">${t.id} · ${t.sponsor}</div>
        <div class="flex-between" style="font-size:12px;margin-bottom:6px">
          <span>适应症：${t.indication}</span>
          <span>${t.centerCount} 个中心</span>
        </div>
        <div class="flex-between" style="font-size:12px;margin-bottom:6px">
          <span>PI：${t.pi}</span>
          <span>开始：${t.startDate}</span>
        </div>
        <div class="divider"></div>
        <div class="flex-between mb-4">
          <span style="font-size:12px;color:var(--gray-600)">入组进度</span>
          <span style="font-size:12px;font-weight:600">${t.enrolled || 0}/${t.targetPatients || 0} 人</span>
        </div>
      </div>
    </div>
  `).join('') || '<div class="empty-state"><div class="empty-icon">🔬</div><p>暂无匹配的试验项目</p></div>';
}

function filterTrials(status) {
  renderTrialCards(status ? CTMS_DATA.trials.filter(t=>t.status===status) : CTMS_DATA.trials);
}

CTMS.completeTrial = async function(trialApiId, trialNo) {
  if (!trialApiId) {
    CTMS.showToast('试验ID无效，无法完结', 'error');
    return;
  }
  if (!confirm(`确认将试验 ${trialNo} 标记为已完成吗？`)) return;
  try {
    await API.trials.update(trialApiId, { status: 'COMPLETED' });
    CTMS.showToast('试验已标记为完成', 'success');
    await loadTrialsFromAPI();
  } catch (error) {
    CTMS.showToast(error.message || '完成功能执行失败', 'error');
  }
};

CTMS.deleteTrial = async function(trialApiId, trialNo) {
  if (!trialApiId) {
    CTMS.showToast('试验ID无效，无法删除', 'error');
    return;
  }
  if (!confirm(`确认删除试验 ${trialNo} 吗？`)) return;
  try {
    await API.trials.delete(trialApiId);
    CTMS.showToast('试验已删除', 'success');
    await loadTrialsFromAPI();
  } catch (error) {
    CTMS.showToast(error.message || '删除失败', 'error');
  }
};

// 全局状态用于保存新建试验的各个步骤数据
window.CTMS_NEW_TRIAL_DATA = {
  step: 1,
  basic: {},
  protocol: {},
  centers: [],
  users: []
};

window.CTMS_EDIT_TRIAL_DATA = null;

function getTrialStorageKey(trialLike) {
  if (!trialLike) return '';
  return trialLike.trial_no || String(trialLike.id || '');
}

function getTrialStorageKeys(trialLike) {
  if (!trialLike) return [];
  const keys = [trialLike.trial_no, String(trialLike.id || '')].filter(Boolean);
  return Array.from(new Set(keys));
}

function pickFromMapByKeys(mapObj, keys) {
  for (const k of keys) {
    if (Object.prototype.hasOwnProperty.call(mapObj, k) && mapObj[k] != null) return mapObj[k];
  }
  return undefined;
}

function safeReadLocalMap(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function safeWriteLocalMap(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn('localStorage write failed:', key, e);
  }
}

function dedupeCenters(centers) {
  const list = Array.isArray(centers) ? centers : [];
  const seen = new Set();
  return list.filter(item => {
    const key = item?.code || item?.id || item?.name;
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function dedupeUsers(users) {
  const list = Array.isArray(users) ? users : [];
  const seen = new Set();
  return list.filter(item => {
    const key = item?.id || item?.email || item?.name;
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function dedupeVisits(visits) {
  const list = Array.isArray(visits) ? visits : [];
  const seen = new Set();
  return list.filter((item, idx) => {
    const key = item?.id || `${item?.name || ''}-${idx}`;
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function loadEditTrialExtraData(trialLike) {
  const extra = trialLike.extra_data || {};
  
  const protocol = extra.protocol || {
    site_cycle: '30',
    enroll_cycle: '12',
    baseline_days: '7',
    followup_cycle: '24',
    blind: 'open',
    visits: []
  };
  const users = dedupeUsers(Array.isArray(extra.users) ? extra.users : []);

  const key = getTrialStorageKey(trialLike);
  const keys = getTrialStorageKeys(trialLike);
  
  let centers = Array.isArray(extra.centers) ? extra.centers : [];

  // 若 API 没有中心明细，则从患者数据中反推该试验已有中心，确保编辑弹窗能回填
  if (!centers.length) {
    const patientCenters = new Set();
    (CTMS_DATA.patients || []).forEach(p => {
      if ((keys.includes(String(p.trialId || ''))) && p.center && p.center !== '-') {
        patientCenters.add(p.center);
      }
    });
    centers = Array.from(patientCenters).map((name, idx) => {
      const found = (CTMS_DATA.centerStats || []).find(c => c.center === name);
      return {
        id: found?.code || `${key}-p-${idx}`,
        code: found?.code || '-',
        name,
        pi: found?.pi || '-',
        target: 0
      };
    });
  }

  return {
    protocol: {
      ...protocol,
      visits: dedupeVisits(protocol.visits || [])
    },
    users,
    centers: dedupeCenters(centers)
  };
}

CTMS.syncEditTrialDataFromDOM = function() {
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  if (!document.getElementById('edit-trial-full-name')) return;

  d.basic = {
    full_name: document.getElementById('edit-trial-full-name').value.trim(),
    trial_no: document.getElementById('edit-trial-no').value.trim(),
    phase: String(document.getElementById('edit-trial-phase').value),
    indication: document.getElementById('edit-trial-indication').value.trim(),
    sponsor: document.getElementById('edit-trial-sponsor').value.trim(),
    drug_name: document.getElementById('edit-trial-drug').value.trim(),
    target_enrollment: document.getElementById('edit-trial-target').value,
    planned_start: document.getElementById('edit-trial-start-date').value,
    status: document.getElementById('edit-trial-status').value
  };

  if (document.getElementById('edit-protocol-site-cycle')) {
    d.protocol = {
      site_cycle: document.getElementById('edit-protocol-site-cycle').value,
      enroll_cycle: document.getElementById('edit-protocol-enroll-cycle').value,
      baseline_days: document.getElementById('edit-protocol-baseline-days').value,
      followup_cycle: document.getElementById('edit-protocol-followup-cycle').value,
      blind: document.querySelector('input[name="edit-blind"]:checked')?.value || 'open',
      visits: Array.from(document.querySelectorAll('#edit-trial-visits-tbody tr'))
        .filter(tr => tr.id !== 'edit-empty-visit')
        .map(tr => ({
          id: tr.getAttribute('data-id'),
          name: tr.querySelector('.visit-name')?.value || '',
          after: tr.querySelector('.visit-after')?.value || '',
          value: tr.querySelector('.visit-value')?.value || '',
          unit: tr.querySelector('.visit-unit')?.value || '天'
        }))
    };
  }

  if (document.getElementById('edit-trial-centers-tbody')) {
    d.centers = dedupeCenters(Array.from(document.querySelectorAll('#edit-trial-centers-tbody tr'))
      .filter(tr => tr.id !== 'edit-empty-center')
      .map(tr => {
        const id = tr.getAttribute('data-id');
        const existing = d.centers.find(c => c.id === id) || {};
        return {
          ...existing,
          target: parseInt(tr.querySelector('.target-input')?.value, 10) || 0
        };
      }));
  }

  if (document.getElementById('edit-trial-users-tbody')) {
    d.users = dedupeUsers(Array.from(document.querySelectorAll('#edit-trial-users-tbody tr'))
      .filter(tr => tr.id !== 'edit-empty-user')
      .map(tr => {
        const id = tr.getAttribute('data-id');
        const existing = d.users.find(u => u.id === id) || {};
        return {
          ...existing,
          role: tr.querySelector('.role-select')?.value || 'PM',
          scope: tr.querySelector('.scope-select')?.value || '本研究'
        };
      }));
  }
};

CTMS.saveEditTrialExtraData = function() {
  // We no longer save extra data to localStorage because it's handled by DB.
};

CTMS.renderEditTrialModal = function() {
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  d.centers = dedupeCenters(d.centers || []);
  d.users = dedupeUsers(d.users || []);
  d.protocol = {
    ...(d.protocol || {}),
    visits: dedupeVisits((d.protocol || {}).visits || [])
  };
  const b = d.basic || {};
  const p = d.protocol || {};
  const centers = d.centers || [];
  const users = d.users || [];

  CTMS.closeModal();
  CTMS.showModal('编辑试验项目', `
    <div class="form-row">
      <div class="form-group"><label class="form-label required">试验名称</label><input id="edit-trial-full-name" class="form-input" value="${b.full_name || ''}"></div>
      <div class="form-group"><label class="form-label required">试验编号</label><input id="edit-trial-no" class="form-input" value="${b.trial_no || ''}" disabled></div>
    </div>
    <div class="form-row col3">
      <div class="form-group"><label class="form-label required">试验阶段</label>
        <select id="edit-trial-phase" class="form-select">
          <option value="8" ${b.phase === '8' ? 'selected' : ''}>I期</option>
          <option value="9" ${b.phase === '9' ? 'selected' : ''}>II期</option>
          <option value="10" ${b.phase === '10' ? 'selected' : ''}>III期</option>
          <option value="11" ${b.phase === '11' ? 'selected' : ''}>IV期</option>
          <option value="12" ${b.phase === '12' ? 'selected' : ''}>上市后临床研究</option>
          <option value="1" ${b.phase === '1' ? 'selected' : ''}>药物临床试验</option>
          <option value="2" ${b.phase === '2' ? 'selected' : ''}>中保研究</option>
          <option value="3" ${b.phase === '3' ? 'selected' : ''}>医疗器械临床试验</option>
          <option value="4" ${b.phase === '4' ? 'selected' : ''}>科研项目其他</option>
          <option value="5" ${b.phase === '5' ? 'selected' : ''}>药物上市后再评价</option>
          <option value="6" ${b.phase === '6' ? 'selected' : ''}>医疗器械上市后再评价</option>
          <option value="7" ${b.phase === '7' ? 'selected' : ''}>其他</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label required">适应症</label><input id="edit-trial-indication" class="form-input" value="${b.indication || ''}"></div>
      <div class="form-group"><label class="form-label required">申办方</label><input id="edit-trial-sponsor" class="form-input" value="${b.sponsor || ''}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">研究药物</label><input id="edit-trial-drug" class="form-input" value="${b.drug_name || ''}"></div>
      <div class="form-group"><label class="form-label required">目标入组例数</label><input id="edit-trial-target" class="form-input" type="number" value="${b.target_enrollment || 100}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">计划启动日期</label><input id="edit-trial-start-date" class="form-input" type="date" value="${b.planned_start || ''}"></div>
      <div class="form-group"><label class="form-label">状态</label>
        <select id="edit-trial-status" class="form-select">
          <option value="PLANNING" ${b.status === 'PLANNING' ? 'selected' : ''}>计划中</option>
          <option value="RECRUITING" ${b.status === 'RECRUITING' ? 'selected' : ''}>入组中</option>
          <option value="ONGOING" ${b.status === 'ONGOING' ? 'selected' : ''}>进行中</option>
          <option value="COMPLETED" ${b.status === 'COMPLETED' ? 'selected' : ''}>已完成</option>
          <option value="SUSPENDED" ${b.status === 'SUSPENDED' ? 'selected' : ''}>已暂停</option>
          <option value="TERMINATED" ${b.status === 'TERMINATED' ? 'selected' : ''}>已终止</option>
        </select>
      </div>
    </div>

    <div class="divider" style="margin:14px 0"></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">中心启动周期(天)</label><input id="edit-protocol-site-cycle" type="number" class="form-input" value="${p.site_cycle || '30'}"></div>
      <div class="form-group"><label class="form-label">入组周期(月)</label><input id="edit-protocol-enroll-cycle" type="number" class="form-input" value="${p.enroll_cycle || '12'}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">基线期数据录入时间(天)</label><input id="edit-protocol-baseline-days" type="number" class="form-input" value="${p.baseline_days || '7'}"></div>
      <div class="form-group"><label class="form-label">随访周期(月)</label><input id="edit-protocol-followup-cycle" type="number" class="form-input" value="${p.followup_cycle || '24'}"></div>
      <div class="form-group"><label class="form-label">随机化与盲法</label>
        <div style="display:flex;gap:16px;margin-top:8px;">
          <label><input type="radio" name="edit-blind" value="open" ${!p.blind || p.blind === 'open' ? 'checked' : ''}> 开放标签</label>
          <label><input type="radio" name="edit-blind" value="single" ${p.blind === 'single' ? 'checked' : ''}> 单盲</label>
          <label><input type="radio" name="edit-blind" value="double" ${p.blind === 'double' ? 'checked' : ''}> 双盲</label>
        </div>
      </div>
    </div>
    <div class="form-group">
      <div class="flex-between mb-8"><label class="form-label" style="margin:0">随访计划</label><button class="btn btn-sm btn-secondary" onclick="CTMS.addEditTrialVisit()">＋ 增加访视</button></div>
      <div class="table-container">
        <table>
          <thead><tr><th>访视名称</th><th>基于(时间点)</th><th>间隔时间</th><th>单位</th><th>操作</th></tr></thead>
          <tbody id="edit-trial-visits-tbody">
            ${!(p.visits && p.visits.length > 0) ? '<tr id="edit-empty-visit"><td colspan="5" style="text-align:center;color:#999">暂未添加访视计划</td></tr>' : p.visits.map(v => `
              <tr data-id="${v.id}">
                <td><input type="text" class="form-input visit-name" value="${v.name || ''}" style="width:100px;padding:4px"></td>
                <td><input type="text" class="form-input visit-after" value="${v.after || ''}" style="width:100px;padding:4px"></td>
                <td><input type="number" class="form-input visit-value" value="${v.value || ''}" style="width:80px;padding:4px"></td>
                <td>
                  <select class="form-select visit-unit" style="padding:4px; width:60px;">
                    <option value="天" ${v.unit==='天'?'selected':''}>天</option>
                    <option value="周" ${v.unit==='周'?'selected':''}>周</option>
                    <option value="月" ${v.unit==='月'?'selected':''}>月</option>
                  </select>
                </td>
                <td><span class="text-danger" style="cursor:pointer" onclick="CTMS.removeEditTrialVisit('${v.id}')">删除</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>

    <div class="divider" style="margin:14px 0"></div>
    <div class="form-group">
      <div class="flex-between mb-8"><label class="form-label" style="margin:0">参与研究中心</label><button class="btn btn-sm btn-secondary" onclick="CTMS.showEditTrialCenterSelector()">＋ 添加中心</button></div>
      <div class="table-container">
        <table>
          <thead><tr><th>中心编号</th><th>中心名称</th><th>目标入组</th><th>PI</th><th>操作</th></tr></thead>
          <tbody id="edit-trial-centers-tbody">
            ${centers.length === 0 ? '<tr id="edit-empty-center"><td colspan="5" style="text-align:center;color:#999">暂未添加中心</td></tr>' : centers.map(c => `
              <tr data-id="${c.id}">
                <td>${c.code || '-'}</td>
                <td>${c.name || '-'}</td>
                <td><input type="number" class="target-input" value="${c.target || 0}" style="width:60px"></td>
                <td>${c.pi || '-'}</td>
                <td><span class="text-danger" style="cursor:pointer" onclick="CTMS.removeEditTrialCenter('${c.id}')">删除</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>

    <div class="divider" style="margin:14px 0"></div>
    <div class="form-group">
      <div class="flex-between mb-8"><label class="form-label" style="margin:0">团队人员授权</label><button class="btn btn-sm btn-secondary" onclick="CTMS.showEditTrialUserSelector()">＋ 添加人员</button></div>
      <div class="table-container">
        <table>
          <thead><tr><th>姓名</th><th>角色</th><th>授权范围</th><th>系统账号</th><th>操作</th></tr></thead>
          <tbody id="edit-trial-users-tbody">
            ${users.length === 0 ? '<tr id="edit-empty-user"><td colspan="5" style="text-align:center;color:#999">暂未添加人员</td></tr>' : users.map(u => `
              <tr data-id="${u.id}">
                <td>${u.name || '-'}</td>
                <td>
                  <select class="form-select role-select" style="padding:4px;font-size:12px">
                    <option value="PM" ${u.role==='PM'?'selected':''}>PM</option>
                    <option value="CRA" ${u.role==='CRA'?'selected':''}>CRA</option>
                    <option value="PI" ${u.role==='PI'?'selected':''}>PI</option>
                    <option value="CRC" ${u.role==='CRC'?'selected':''}>CRC</option>
                  </select>
                </td>
                <td>
                  <select class="form-select scope-select" style="padding:4px;font-size:12px">
                    <option value="本研究" ${u.scope==='本研究'?'selected':''}>本研究</option>
                    <option value="全局" ${u.scope==='全局'?'selected':''}>全局</option>
                    ${centers.map(c => `<option value="${c.name}" ${u.scope===c.name?'selected':''}>${c.name}</option>`).join('')}
                  </select>
                </td>
                <td>${u.email || '-'}</td>
                <td><span class="text-danger" style="cursor:pointer" onclick="CTMS.removeEditTrialUser('${u.id}')">删除</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `, `<button class="btn btn-secondary" onclick="CTMS.closeModal()">取消</button><button class="btn btn-primary" onclick="CTMS.saveRwsProjectAll('${d.trialId}')">保存修改</button>`);
};

CTMS.addEditTrialVisit = function() {
  CTMS.syncEditTrialDataFromDOM();
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  if (!d.protocol.visits) d.protocol.visits = [];
  const vCount = d.protocol.visits.length;
  d.protocol.visits.push({
    id: 'ev' + Date.now(),
    name: `访视${vCount + 1}`,
    after: vCount === 0 ? '基线' : `访视${vCount}`,
    value: vCount === 0 ? 7 : 1,
    unit: vCount === 0 ? '天' : '月'
  });
  CTMS.renderEditTrialModal();
};

CTMS.removeEditTrialVisit = function(id) {
  CTMS.syncEditTrialDataFromDOM();
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  d.protocol.visits = (d.protocol.visits || []).filter(v => v.id !== id);
  CTMS.renderEditTrialModal();
};

CTMS.showEditTrialCenterSelector = function() {
  CTMS.syncEditTrialDataFromDOM();
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  const addedCodes = (d.centers || []).map(c => c.code);
  const available = (CTMS_DATA.centerStats || []).filter(c => !addedCodes.includes(c.code));
  if (available.length === 0) {
    CTMS.showToast('没有更多可选的研究中心', 'info');
    return;
  }
  const html = `
    <div class="form-group"><label class="form-label">选择中心（可多选）</label>
      <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--gray-300); border-radius: 4px; padding: 8px;">
        ${available.map(c => `
          <label style="display:flex; align-items:center; gap:8px; margin-bottom:8px; cursor:pointer;">
            <input type="checkbox" name="edit-trial-add-center-checkbox" value="${c.code}">
            ${c.code} - ${c.center}
          </label>
        `).join('')}
      </div>
    </div>
  `;
  const footer = `<button class="btn btn-secondary" onclick="CTMS.renderEditTrialModal()">取消</button><button class="btn btn-primary" onclick="CTMS.addEditTrialCenter()">确认添加</button>`;
  CTMS.showModal('添加研究中心', html, footer);
};

CTMS.addEditTrialCenter = function() {
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  const checkboxes = document.querySelectorAll('input[name="edit-trial-add-center-checkbox"]:checked');
  if (checkboxes.length === 0) {
    CTMS.showToast('请至少选择一个中心', 'warning');
    return;
  }
  let addedCount = 0;
  checkboxes.forEach(cb => {
    const code = cb.value;
    const center = (CTMS_DATA.centerStats || []).find(c => c.code === code);
    const exists = (d.centers || []).some(c => c.code === code);
    if (center && !exists) {
      d.centers.push({ id: center.code, code: center.code, name: center.center, pi: center.pi || '-', target: 0 });
      addedCount += 1;
    }
  });
  CTMS.showToast(addedCount > 0 ? `已成功添加 ${addedCount} 个中心` : '选择的中心已存在于列表中', addedCount > 0 ? 'success' : 'info');
  CTMS.renderEditTrialModal();
};

CTMS.removeEditTrialCenter = function(id) {
  CTMS.syncEditTrialDataFromDOM();
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  d.centers = (d.centers || []).filter(c => c.id !== id);
  CTMS.renderEditTrialModal();
};

CTMS.showEditTrialUserSelector = function() {
  CTMS.syncEditTrialDataFromDOM();
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  const addedIds = (d.users || []).map(u => u.id);
  const available = (CTMS_DATA.users || []).filter(u => !addedIds.includes(u.id));
  if (available.length === 0) {
    CTMS.showToast('没有更多可选的人员', 'info');
    return;
  }
  const html = `
    <div class="form-group"><label class="form-label">选择人员（可多选）</label>
      <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--gray-300); border-radius: 4px; padding: 8px;">
        ${available.map(u => `
          <label style="display:flex; align-items:center; gap:8px; margin-bottom:8px; cursor:pointer;">
            <input type="checkbox" name="edit-trial-add-user-checkbox" value="${u.id}">
            ${u.name} (${u.role} - ${u.dept})
          </label>
        `).join('')}
      </div>
    </div>
  `;
  const footer = `<button class="btn btn-secondary" onclick="CTMS.renderEditTrialModal()">取消</button><button class="btn btn-primary" onclick="CTMS.addEditTrialUser()">确认添加</button>`;
  CTMS.showModal('添加人员', html, footer);
};

CTMS.addEditTrialUser = function() {
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  const checkboxes = document.querySelectorAll('input[name="edit-trial-add-user-checkbox"]:checked');
  if (checkboxes.length === 0) {
    CTMS.showToast('请至少选择一个人员', 'warning');
    return;
  }
  let addedCount = 0;
  checkboxes.forEach(cb => {
    const id = cb.value;
    const user = (CTMS_DATA.users || []).find(u => u.id === id);
    const exists = (d.users || []).some(u => u.id === id);
    if (user && !exists) {
      d.users.push({
        id: user.id,
        name: user.name,
        role: user.role === '主要研究者' ? 'PI' : (user.role === '临床监查员(CRA)' ? 'CRA' : 'PM'),
        scope: '本研究',
        email: user.email || `${user.id}@ctms.com`
      });
      addedCount += 1;
    }
  });
  CTMS.showToast(addedCount > 0 ? `已成功添加 ${addedCount} 个人员` : '选择的人员已存在于授权列表中', addedCount > 0 ? 'success' : 'info');
  CTMS.renderEditTrialModal();
};

CTMS.removeEditTrialUser = function(id) {
  CTMS.syncEditTrialDataFromDOM();
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d) return;
  d.users = (d.users || []).filter(u => u.id !== id);
  CTMS.renderEditTrialModal();
};

CTMS.showNewTrialModal = function(step = 1) {
  window.CTMS_NEW_TRIAL_DATA.step = step;
  const d = window.CTMS_NEW_TRIAL_DATA;
  
  // 保存当前步骤的数据
  if (document.getElementById('trial-full-name')) {
    d.basic = {
      full_name: document.getElementById('trial-full-name').value.trim(),
      trial_no: document.getElementById('trial-no').value.trim(),
      contract_no: document.getElementById('trial-contract-no')?.value || '',
      phase: document.getElementById('trial-phase').value,
      indication: document.getElementById('trial-indication').value.trim(),
      sponsor: document.getElementById('trial-sponsor').value.trim(),
      drug_name: document.getElementById('trial-drug').value.trim(),
      target: document.getElementById('trial-target').value,
      start_date: document.getElementById('trial-start-date').value,
      desc: document.getElementById('trial-desc').value.trim()
    };
  } else if (document.getElementById('protocol-site-cycle')) {
    d.protocol.site_cycle = document.getElementById('protocol-site-cycle').value;
    d.protocol.enroll_cycle = document.getElementById('protocol-enroll-cycle').value;
    d.protocol.baseline_days = document.getElementById('protocol-baseline-days').value;
    d.protocol.followup_cycle = document.getElementById('protocol-followup-cycle').value;
    d.protocol.blind = document.querySelector('input[name="blind"]:checked')?.value || 'open';
    
    Array.from(document.querySelectorAll('#trial-visits-tbody tr')).filter(tr => tr.id !== 'empty-visit').forEach(tr => {
      const id = tr.getAttribute('data-id');
      const existing = (d.protocol.visits || []).find(v => v.id === id);
      if (existing) {
        existing.name = tr.querySelector('.visit-name').value;
        existing.after = tr.querySelector('.visit-after').value;
        existing.value = tr.querySelector('.visit-value').value;
        existing.unit = tr.querySelector('.visit-unit').value;
      }
    });
  } else if (document.getElementById('trial-centers-tbody')) {
    const currentTbodys = document.querySelectorAll('#trial-centers-tbody tr');
    if (currentTbodys.length > 0 && currentTbodys[0].id !== 'empty-center') {
      Array.from(currentTbodys).forEach(tr => {
        const id = tr.getAttribute('data-id');
        const targetInput = tr.querySelector('.target-input');
        const existing = d.centers.find(c => c.id === id);
        if (existing) {
          existing.target = targetInput ? parseInt(targetInput.value) || 0 : 0;
        }
      });
    }
  } else if (document.getElementById('trial-users-tbody')) {
    const currentTbodys = document.querySelectorAll('#trial-users-tbody tr');
    if (currentTbodys.length > 0 && currentTbodys[0].id !== 'empty-user') {
      Array.from(currentTbodys).forEach(tr => {
        const id = tr.getAttribute('data-id');
        const role = tr.querySelector('.role-select')?.value;
        const scope = tr.querySelector('.scope-select')?.value;
        const existing = d.users.find(u => u.id === id);
        if (existing) {
          existing.role = role;
          existing.scope = scope;
        }
      });
    }
  }

  let bodyHtml = '';
  let footerHtml = '';

  const stepBar = `
    <div class="step-bar">
      <div class="step-item ${step>=1?'active':''}"><div class="step-circle">1</div><div class="step-label">基本信息</div></div>
      <div class="step-item ${step>=2?'active':''}"><div class="step-circle">2</div><div class="step-label">方案配置</div></div>
      <div class="step-item ${step>=3?'active':''}"><div class="step-circle">3</div><div class="step-label">中心分配</div></div>
      <div class="step-item ${step>=4?'active':''}"><div class="step-circle">4</div><div class="step-label">人员授权</div></div>
    </div>
  `;

  if (step === 1) {
    bodyHtml = `
      ${stepBar}
      <div class="form-row">
        <div class="form-group"><label class="form-label required">试验名称</label><input id="trial-full-name" class="form-input" placeholder="请输入完整试验名称" value="${d.basic.full_name || ''}"></div>
        <div class="form-group"><label class="form-label required">试验编号</label><input id="trial-no" class="form-input" placeholder="如：CT2026001" value="${d.basic.trial_no || 'CT2026'+String(Date.now()).slice(-4)}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">合同编号</label>
          <select id="trial-contract-no" class="form-select">
            <option value="">请选择（选填）</option>
            ${(CTMS_DATA.contracts || []).map(c => `<option value="${c.id}" ${d.basic.contract_no === c.id ? 'selected' : ''}>${c.id} - ${c.sponsor}</option>`).join('')}
          </select>
        </div>
      </div>
      <div class="form-row col3">
        <div class="form-group"><label class="form-label required">试验阶段</label><select id="trial-phase" class="form-select">
          <option value="8" ${d.basic.phase==='8'?'selected':''}>I期</option>
          <option value="9" ${d.basic.phase==='9'?'selected':''}>II期</option>
          <option value="10" ${d.basic.phase==='10'?'selected':''}>III期</option>
          <option value="11" ${d.basic.phase==='11'?'selected':''}>IV期</option>
          <option value="12" ${d.basic.phase==='12'?'selected':''}>上市后临床研究</option>
          <option value="1" ${d.basic.phase==='1'?'selected':''}>药物临床试验</option>
          <option value="2" ${d.basic.phase==='2'?'selected':''}>中保研究</option>
          <option value="3" ${d.basic.phase==='3'?'selected':''}>医疗器械临床试验</option>
          <option value="4" ${d.basic.phase==='4'?'selected':''}>科研项目其他</option>
          <option value="5" ${d.basic.phase==='5'?'selected':''}>药物上市后再评价</option>
          <option value="6" ${d.basic.phase==='6'?'selected':''}>医疗器械上市后再评价</option>
          <option value="7" ${d.basic.phase==='7'?'selected':''}>其他</option>
        </select></div>
        <div class="form-group"><label class="form-label required">适应症</label><input id="trial-indication" class="form-input" placeholder="如：非小细胞肺癌" value="${d.basic.indication || ''}"></div>
        <div class="form-group"><label class="form-label required">申办方</label><input id="trial-sponsor" class="form-input" placeholder="申办方名称" value="${d.basic.sponsor || ''}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">研究药物</label><input id="trial-drug" class="form-input" placeholder="药物名称/编号" value="${d.basic.drug_name || ''}"></div>
        <div class="form-group"><label class="form-label required">目标入组例数</label><input id="trial-target" class="form-input" type="number" placeholder="100" value="${d.basic.target || '100'}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">计划启动日期</label><input id="trial-start-date" class="form-input" type="date" value="${d.basic.start_date || ''}"></div>
      </div>
      <div class="form-group"><label class="form-label">试验概述</label><textarea id="trial-desc" class="form-textarea" placeholder="简述试验背景、目的、设计...">${d.basic.desc || ''}</textarea></div>
    `;
    footerHtml = `<button class="btn btn-secondary" onclick="CTMS.closeModal()">关闭</button><button class="btn btn-primary" onclick="CTMS.showNewTrialModal(2)">下一步</button>`;
  } else if (step === 2) {
    // 保存当前步骤(如果是从步骤2跳走的话，由于这里是渲染逻辑，保存逻辑应该在切换时执行)
    // 但目前逻辑是切换时在目标步骤检查上一部的DOM，由于切换是重新调用 showNewTrialModal(N)，
    // 我们需要在顶部判断如果有 step2 的 DOM 就保存。
    bodyHtml = `
      ${stepBar}
      <div class="form-row">
        <div class="form-group"><label class="form-label required">中心启动周期(天)</label>
          <input id="protocol-site-cycle" type="number" class="form-input" placeholder="例如：30" value="${d.protocol.site_cycle || '30'}">
        </div>
        <div class="form-group"><label class="form-label required">入组周期(月)</label>
          <input id="protocol-enroll-cycle" type="number" class="form-input" placeholder="例如：12" value="${d.protocol.enroll_cycle || '12'}">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label required">基线期数据录入时间(天)</label>
          <input id="protocol-baseline-days" type="number" class="form-input" placeholder="例如：7" value="${d.protocol.baseline_days || '7'}">
        </div>
        <div class="form-group"><label class="form-label required">随访周期(月)</label>
          <input id="protocol-followup-cycle" type="number" class="form-input" placeholder="例如：24" value="${d.protocol.followup_cycle || '24'}">
        </div>
        <div class="form-group"><label class="form-label">随机化与盲法</label>
          <div style="display:flex;gap:16px;margin-top:8px;">
            <label><input type="radio" name="blind" value="open" ${!d.protocol.blind || d.protocol.blind==='open' ? 'checked':''}> 开放标签</label>
            <label><input type="radio" name="blind" value="single" ${d.protocol.blind==='single' ? 'checked':''}> 单盲</label>
            <label><input type="radio" name="blind" value="double" ${d.protocol.blind==='double' ? 'checked':''}> 双盲</label>
          </div>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group" style="width:100%"><label class="form-label required">访视计划设置</label>
          <div class="table-container">
            <table>
              <thead><tr><th>访视名称</th><th>基于(时间点)</th><th>间隔时间</th><th>单位</th><th>操作</th></tr></thead>
              <tbody id="trial-visits-tbody">
                ${!(d.protocol.visits && d.protocol.visits.length > 0) ? '<tr id="empty-visit"><td colspan="5" style="text-align:center;color:#999">暂未添加访视计划</td></tr>' : d.protocol.visits.map(v => `
                  <tr data-id="${v.id}">
                    <td><input type="text" class="form-input visit-name" value="${v.name}" style="width:100px;padding:4px"></td>
                    <td><input type="text" class="form-input visit-after" value="${v.after}" style="width:100px;padding:4px"></td>
                    <td><input type="number" class="form-input visit-value" value="${v.value}" style="width:80px;padding:4px"></td>
                    <td>
                      <select class="form-select visit-unit" style="padding:4px; width:60px;">
                        <option value="天" ${v.unit==='天'?'selected':''}>天</option>
                        <option value="周" ${v.unit==='周'?'selected':''}>周</option>
                        <option value="月" ${v.unit==='月'?'selected':''}>月</option>
                      </select>
                    </td>
                    <td><span class="text-danger" style="cursor:pointer" onclick="CTMS.removeTrialVisit('${v.id}')">删除</span></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
          <button class="btn btn-sm btn-secondary mt-8" style="margin-top:8px" onclick="CTMS.addTrialVisit()">＋ 增加访视</button>
        </div>
      </div>
      <div class="form-group"><label class="form-label">上传试验方案 (PDF/Word)</label>
        <div class="upload-area" style="padding:20px;text-align:center;border:1px dashed #ccc;border-radius:4px;">
           <span style="font-size:24px">📄</span><br>点击或拖拽文件到此处上传
        </div>
      </div>
    `;
    footerHtml = `<button class="btn btn-secondary" onclick="CTMS.closeModal()">关闭</button><button class="btn btn-secondary" onclick="CTMS.showNewTrialModal(1)">上一步</button><button class="btn btn-primary" onclick="CTMS.showNewTrialModal(3)">下一步</button>`;
  } else if (step === 3) {
    bodyHtml = `
      ${stepBar}
      <div class="flex-between mb-8">
        <label class="form-label" style="margin:0">参与研究中心</label>
        <button class="btn btn-sm btn-secondary" onclick="CTMS.showTrialCenterSelector()">＋ 添加中心</button>
      </div>
      <div class="table-container">
        <table>
          <thead><tr><th>中心编号</th><th>中心名称</th><th>目标入组</th><th>PI</th><th>操作</th></tr></thead>
          <tbody id="trial-centers-tbody">
            ${d.centers.length === 0 ? '<tr id="empty-center"><td colspan="5" style="text-align:center;color:#999">暂未添加中心</td></tr>' : d.centers.map(c => `
              <tr data-id="${c.id}">
                <td>${c.code}</td>
                <td>${c.name}</td>
                <td><input type="number" class="target-input" value="${c.target || 0}" style="width:60px" onchange="window.CTMS_NEW_TRIAL_DATA.centers.find(x=>x.id==='${c.id}').target=parseInt(this.value)||0"></td>
                <td>${c.pi}</td>
                <td><span class="text-danger" style="cursor:pointer" onclick="CTMS.removeTrialCenter('${c.id}')">删除</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
    footerHtml = `<button class="btn btn-secondary" onclick="CTMS.closeModal()">关闭</button><button class="btn btn-secondary" onclick="CTMS.showNewTrialModal(2)">上一步</button><button class="btn btn-primary" onclick="CTMS.showNewTrialModal(4)">下一步</button>`;
  } else if (step === 4) {
    bodyHtml = `
      ${stepBar}
      <div class="flex-between mb-8">
        <label class="form-label" style="margin:0">团队人员授权</label>
        <button class="btn btn-sm btn-secondary" onclick="CTMS.showTrialUserSelector()">＋ 添加人员</button>
      </div>
      <div class="table-container">
        <table>
          <thead><tr><th>姓名</th><th>角色</th><th>授权范围</th><th>系统账号</th><th>操作</th></tr></thead>
          <tbody id="trial-users-tbody">
            ${d.users.length === 0 ? '<tr id="empty-user"><td colspan="5" style="text-align:center;color:#999">暂未添加人员</td></tr>' : d.users.map(u => `
              <tr data-id="${u.id}">
                <td>${u.name}</td>
                <td>
                  <select class="form-select role-select" style="padding:4px;font-size:12px" onchange="window.CTMS_NEW_TRIAL_DATA.users.find(x=>x.id==='${u.id}').role=this.value">
                    <option value="PM" ${u.role==='PM'?'selected':''}>PM</option>
                    <option value="CRA" ${u.role==='CRA'?'selected':''}>CRA</option>
                    <option value="PI" ${u.role==='PI'?'selected':''}>PI</option>
                    <option value="CRC" ${u.role==='CRC'?'selected':''}>CRC</option>
                  </select>
                </td>
                <td>
                  <select class="form-select scope-select" style="padding:4px;font-size:12px" onchange="window.CTMS_NEW_TRIAL_DATA.users.find(x=>x.id==='${u.id}').scope=this.value">
                    <option value="本研究" ${u.scope==='本研究'?'selected':''}>本研究</option>
                    <option value="全局" ${u.scope==='全局'?'selected':''}>全局</option>
                    ${d.centers.map(c => `<option value="${c.name}" ${u.scope===c.name?'selected':''}>${c.name}</option>`).join('')}
                  </select>
                </td>
                <td>${u.email}</td>
                <td><span class="text-danger" style="cursor:pointer" onclick="CTMS.removeTrialUser('${u.id}')">删除</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <div class="alert alert-info mt-16" style="padding:10px;background:#e0f2fe;color:#0369a1;border-radius:4px;font-size:13px;">
        ℹ️ 创建试验后，系统将自动为授权人员发送通知邮件及初始密码。
      </div>
    `;
    footerHtml = `<button class="btn btn-secondary" onclick="CTMS.closeModal()">关闭</button><button class="btn btn-secondary" onclick="CTMS.showNewTrialModal(3)">上一步</button><button class="btn btn-primary" onclick="CTMS.createTrial()">完成并创建</button>`;
  }

  CTMS.closeModal();
  CTMS.showModal('新建试验项目', bodyHtml, footerHtml);
};

CTMS.showTrialCenterSelector = function() {
  // 如果之前在第三步界面，先尝试保存当前页面正在编辑的数据，防止被覆盖丢失
  if (document.getElementById('trial-centers-tbody')) {
    const currentTbodys = document.querySelectorAll('#trial-centers-tbody tr');
    if (currentTbodys.length > 0 && currentTbodys[0].id !== 'empty-center') {
      Array.from(currentTbodys).forEach(tr => {
        const id = tr.getAttribute('data-id');
        const targetInput = tr.querySelector('.target-input');
        const existing = window.CTMS_NEW_TRIAL_DATA.centers.find(c => c.id === id);
        if (existing) {
          existing.target = targetInput ? parseInt(targetInput.value) || 0 : 0;
        }
      });
    }
  }

  const centers = CTMS_DATA.centerStats || [];
  const addedIds = window.CTMS_NEW_TRIAL_DATA.centers.map(c => c.id);
  const available = centers.filter(c => !addedIds.includes(c.code));
  
  if (available.length === 0) {
    CTMS.showToast('没有更多可选的研究中心', 'info');
    return;
  }

  const html = `
    <div class="form-group"><label class="form-label">选择中心（可多选）</label>
      <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--gray-300); border-radius: 4px; padding: 8px;">
        ${available.map(c => `
          <label style="display:flex; align-items:center; gap:8px; margin-bottom:8px; cursor:pointer;">
            <input type="checkbox" name="trial-add-center-checkbox" value="${c.code}">
            ${c.code} - ${c.center}
          </label>
        `).join('')}
      </div>
    </div>
  `;
  const footer = `
    <button class="btn btn-secondary" onclick="CTMS.showNewTrialModal(3)">取消</button>
    <button class="btn btn-primary" onclick="CTMS.addTrialCenter()">确认添加</button>
  `;
  CTMS.showModal('添加研究中心', html, footer);
};

CTMS.addTrialCenter = function() {
  const checkboxes = document.querySelectorAll('input[name="trial-add-center-checkbox"]:checked');
  if (checkboxes.length === 0) {
    CTMS.showToast('请至少选择一个中心', 'warning');
    return;
  }
  
  let addedCount = 0;
  checkboxes.forEach(cb => {
    const code = cb.value;
    const center = (CTMS_DATA.centerStats || []).find(c => c.code === code);
    // 检查是否已经存在于 d.centers 中
    const existingIndex = window.CTMS_NEW_TRIAL_DATA.centers.findIndex(c => c.code === code);
    if (center && existingIndex === -1) {
      window.CTMS_NEW_TRIAL_DATA.centers.push({
        id: center.code,
        code: center.code,
        name: center.center,
        pi: center.pi || '-',
        target: 0
      });
      addedCount++;
    }
  });

  if (addedCount > 0) {
    CTMS.showToast(`已成功添加 ${addedCount} 个中心`, 'success');
  } else {
    CTMS.showToast('选择的中心已存在于列表中', 'info');
  }
  CTMS.showNewTrialModal(3);
};

CTMS.removeTrialCenter = function(id) {
  window.CTMS_NEW_TRIAL_DATA.centers = window.CTMS_NEW_TRIAL_DATA.centers.filter(c => c.id !== id);
  CTMS.showNewTrialModal(3);
};

CTMS.showTrialUserSelector = function() {
  // 如果之前在第四步界面，先尝试保存当前页面正在编辑的数据，防止被覆盖丢失
  if (document.getElementById('trial-users-tbody')) {
    const currentTbodys = document.querySelectorAll('#trial-users-tbody tr');
    if (currentTbodys.length > 0 && currentTbodys[0].id !== 'empty-user') {
      Array.from(currentTbodys).forEach(tr => {
        const id = tr.getAttribute('data-id');
        const role = tr.querySelector('.role-select')?.value;
        const scope = tr.querySelector('.scope-select')?.value;
        const existing = window.CTMS_NEW_TRIAL_DATA.users.find(u => u.id === id);
        if (existing) {
          existing.role = role;
          existing.scope = scope;
        }
      });
    }
  }

  const users = CTMS_DATA.users || [];
  const addedIds = window.CTMS_NEW_TRIAL_DATA.users.map(u => u.id);
  const available = users.filter(u => !addedIds.includes(u.id));
  
  if (available.length === 0) {
    CTMS.showToast('没有更多可选的人员', 'info');
    return;
  }

  const html = `
    <div class="form-group"><label class="form-label">选择人员（可多选）</label>
      <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--gray-300); border-radius: 4px; padding: 8px;">
        ${available.map(u => `
          <label style="display:flex; align-items:center; gap:8px; margin-bottom:8px; cursor:pointer;">
            <input type="checkbox" name="trial-add-user-checkbox" value="${u.id}">
            ${u.name} (${u.role} - ${u.dept})
          </label>
        `).join('')}
      </div>
    </div>
  `;
  const footer = `
    <button class="btn btn-secondary" onclick="CTMS.showNewTrialModal(4)">取消</button>
    <button class="btn btn-primary" onclick="CTMS.addTrialUser()">确认添加</button>
  `;
  CTMS.showModal('添加人员', html, footer);
};

CTMS.addTrialUser = function() {
  const checkboxes = document.querySelectorAll('input[name="trial-add-user-checkbox"]:checked');
  if (checkboxes.length === 0) {
    CTMS.showToast('请至少选择一个人员', 'warning');
    return;
  }
  
  let addedCount = 0;
  checkboxes.forEach(cb => {
    const id = cb.value;
    const user = (CTMS_DATA.users || []).find(u => u.id === id);
    // 检查是否已经存在于 d.users 中
    const existingIndex = window.CTMS_NEW_TRIAL_DATA.users.findIndex(u => u.id === id);
    if (user && existingIndex === -1) {
      window.CTMS_NEW_TRIAL_DATA.users.push({
        id: user.id,
        name: user.name,
        role: user.role === '主要研究者' ? 'PI' : (user.role === '临床监查员(CRA)' ? 'CRA' : 'PM'),
        scope: '本研究',
        email: user.email || `${user.id}@ctms.com`
      });
      addedCount++;
    }
  });

  if (addedCount > 0) {
    CTMS.showToast(`已成功添加 ${addedCount} 个人员`, 'success');
  } else {
    CTMS.showToast('选择的人员已存在于授权列表中', 'info');
  }
  CTMS.showNewTrialModal(4);
};

CTMS.removeTrialUser = function(id) {
  window.CTMS_NEW_TRIAL_DATA.users = window.CTMS_NEW_TRIAL_DATA.users.filter(u => u.id !== id);
  CTMS.showNewTrialModal(4);
};

CTMS.addTrialVisit = function() {
  const d = window.CTMS_NEW_TRIAL_DATA;
  if (!d.protocol.visits) d.protocol.visits = [];
  
  // 自动推断默认名称和基准点
  const vCount = d.protocol.visits.length;
  let defaultName = `访视${vCount + 1}`;
  let defaultAfter = vCount === 0 ? '基线' : `访视${vCount}`;
  
  d.protocol.visits.push({
    id: 'v' + Date.now(),
    name: defaultName,
    after: defaultAfter,
    value: vCount === 0 ? 7 : 1,
    unit: vCount === 0 ? '天' : '月'
  });
  
  // 保存其他输入框数据，防止丢失
  if (document.getElementById('protocol-site-cycle')) {
    d.protocol.site_cycle = document.getElementById('protocol-site-cycle').value;
    d.protocol.enroll_cycle = document.getElementById('protocol-enroll-cycle').value;
    d.protocol.baseline_days = document.getElementById('protocol-baseline-days').value;
    d.protocol.followup_cycle = document.getElementById('protocol-followup-cycle').value;
    d.protocol.blind = document.querySelector('input[name="blind"]:checked')?.value || 'open';
  }
  
  CTMS.showNewTrialModal(2);
};

CTMS.removeTrialVisit = function(id) {
  const d = window.CTMS_NEW_TRIAL_DATA;
  if (d.protocol.visits) {
    d.protocol.visits = d.protocol.visits.filter(v => v.id !== id);
  }
  
  if (document.getElementById('protocol-site-cycle')) {
    d.protocol.site_cycle = document.getElementById('protocol-site-cycle').value;
    d.protocol.enroll_cycle = document.getElementById('protocol-enroll-cycle').value;
    d.protocol.baseline_days = document.getElementById('protocol-baseline-days').value;
    d.protocol.followup_cycle = document.getElementById('protocol-followup-cycle').value;
    d.protocol.blind = document.querySelector('input[name="blind"]:checked')?.value || 'open';
  }
  
  CTMS.showNewTrialModal(2);
};

// 创建试验 - 调用API保存到数据库
CTMS.createTrial = async function() {
  // 如果当前在第四步页面，先触发一次保存
  if (document.getElementById('trial-users-tbody')) {
    const currentTbodys = document.querySelectorAll('#trial-users-tbody tr');
    if (currentTbodys.length > 0 && currentTbodys[0].id !== 'empty-user') {
      Array.from(currentTbodys).forEach(tr => {
        const id = tr.getAttribute('data-id');
        const role = tr.querySelector('.role-select')?.value;
        const scope = tr.querySelector('.scope-select')?.value;
        const existing = window.CTMS_NEW_TRIAL_DATA.users.find(u => u.id === id);
        if (existing) {
          existing.role = role;
          existing.scope = scope;
        }
      });
    }
  }

  const d = window.CTMS_NEW_TRIAL_DATA.basic;
  const selectedCenters = (window.CTMS_NEW_TRIAL_DATA.centers || []).map(c => c.name).filter(Boolean);
  const trialData = {
    trial_no: d.trial_no,
    short_name: (d.full_name || '').slice(0, 50),
    full_name: d.full_name,
    phase: d.phase,
    type: d.type,
    indication: d.indication,
    sponsor: d.sponsor,
    drug_name: d.drug_name || null,
    target_enrollment: parseInt(d.target) || 100,
    planned_start: d.start_date || null,
    centers: window.CTMS_NEW_TRIAL_DATA.centers || [],
    users: window.CTMS_NEW_TRIAL_DATA.users || [],
    user_token: window.API?.token?.getAccessToken() || localStorage.getItem('access_token'),
    extra_data: {
      centers: window.CTMS_NEW_TRIAL_DATA.centers || [],
      users: window.CTMS_NEW_TRIAL_DATA.users || [],
      protocol: window.CTMS_NEW_TRIAL_DATA.protocol || {}
    }
  };
  
  // 验证必填字段
  if (!trialData.trial_no || !trialData.full_name || !trialData.indication || !trialData.sponsor) {
    CTMS.showToast('请填写基本信息中的所有必填字段', 'error');
    CTMS.showNewTrialModal(1);
    return;
  }
  
  try {
    const result = await API.trials.create(trialData);
    const createdId = result?.data?.id;
    if (!createdId) {
      throw new Error('创建接口未返回有效ID');
    }

    // Removed localStorage extra data saving logic since it's now saved in DB via extra_data field

    let visible = false;
    for (let i = 0; i < 6; i++) {
      const listRes = await API.trials.list({ page: 1, page_size: 100, keyword: trialData.trial_no });
      const items = (listRes && listRes.items) ? listRes.items : [];
      if (items.some(x => x.id === createdId || x.trial_no === trialData.trial_no)) {
        visible = true;
        break;
      }
      await new Promise(r => setTimeout(r, 500));
    }
    if (!visible) {
      throw new Error('创建成功但列表暂不可见，请稍后刷新');
    }
    
    // 如果返回数据中包含 trial_code（外部接口同步结果），进行差异化提示
    if (result && result.data && result.data.trial_code) {
      CTMS.showToast(`试验创建成功！外部项目号：${result.data.trial_code}`, 'success');
    } else {
      CTMS.showToast('试验创建成功，但外部系统可能暂未同步。', 'success');
    }
    
    // 强制清理创建弹窗相关的 DOM
    CTMS.closeModal();
    
    // 清理全局状态，以便下次新建
    window.CTMS_NEW_TRIAL_DATA = { step: 1, basic: {}, protocol: {}, centers: [], users: [] };
    
    CTMS.navigate('trials');
  } catch (error) {
    console.error('创建试验失败:', error);
    CTMS.showToast(error.message || '创建失败，请重试', 'error');
    // 出现错误不关闭窗口
  }
};

// 编辑试验 - 从API获取数据并显示编辑弹窗
CTMS.editTrial = async function(trialId) {
  try {
    // 从API获取试验详情
    const trial = await API.trials.get(trialId);
    const t = trial.data || trial;
    const extras = loadEditTrialExtraData(t);
    window.CTMS_EDIT_TRIAL_DATA = {
      trialId,
      trialNo: t.trial_no || '',
      basic: {
        full_name: t.full_name || '',
        trial_no: t.trial_no || '',
        phase: t.phase || '9',
        indication: t.indication || '',
        sponsor: t.sponsor || '',
        drug_name: t.drug_name || '',
        target_enrollment: t.target_enrollment || 100,
        planned_start: t.planned_start || '',
        status: t.status || 'PLANNING'
      },
      protocol: extras.protocol,
      centers: extras.centers,
      users: extras.users
    };
    CTMS.renderEditTrialModal();
  } catch (error) {
    console.error('获取试验详情失败:', error);
    CTMS.showToast(error.message || '获取试验信息失败', 'error');
  }
};

// 更新试验 - 调用API保存修改
CTMS.updateTrial = async function(trialId) {
  CTMS.syncEditTrialDataFromDOM();
  const d = window.CTMS_EDIT_TRIAL_DATA;
  if (!d || !d.basic) {
    CTMS.showToast('编辑数据状态异常，请关闭后重试', 'error');
    return;
  }
  const targetEnrollment = parseInt(document.getElementById('edit-trial-target').value);
  
  const trialData = {
    short_name: d.basic.full_name.slice(0, 50),
    full_name: d.basic.full_name,
    phase: d.basic.phase,
    indication: d.basic.indication,
    sponsor: d.basic.sponsor,
    drug_name: d.basic.drug_name || null,
    target_enrollment: isNaN(targetEnrollment) ? 100 : targetEnrollment,
    planned_start: d.basic.planned_start || null,
    status: d.basic.status,
    extra_data: {
      centers: d.centers || [],
      users: d.users || [],
      protocol: d.protocol || {}
    }
  };
  
  // 验证必填字段
  if (!trialData.full_name || !trialData.indication || !trialData.sponsor || isNaN(targetEnrollment)) {
    CTMS.showToast('请完整填写带有星号的必填字段', 'error');
    return;
  }
  
  if (targetEnrollment <= 0) {
    CTMS.showToast('目标入组例数必须大于0', 'error');
    return;
  }
  
  try {
    await API.trials.update(trialId, trialData);
    CTMS.saveEditTrialExtraData();
    CTMS.showToast('试验信息已更新！', 'success');
    CTMS.closeModal();
    // 刷新试验详情
    CTMS.navigate('trial-detail', { trialId: trialId });
  } catch (error) {
    console.error('更新试验失败:', error);
    CTMS.showToast(error.message || '更新失败，请重试', 'error');
  }
};

  CTMS.saveRwsProjectAll = async function(trialId) {
    CTMS.syncEditTrialDataFromDOM();
    const d = window.CTMS_EDIT_TRIAL_DATA;
    if (!d || !d.basic) {
      CTMS.showToast('编辑数据状态异常，请关闭后重试', 'error');
      return;
    }
    const targetEnrollment = parseInt(document.getElementById('edit-trial-target').value);
    
    const trialData = {
      short_name: d.basic.full_name.slice(0, 50),
      full_name: d.basic.full_name,
      phase: d.basic.phase,
      indication: d.basic.indication,
      sponsor: d.basic.sponsor,
      drug_name: d.basic.drug_name || null,
      target_enrollment: isNaN(targetEnrollment) ? 100 : targetEnrollment,
      planned_start: d.basic.planned_start || null,
      status: d.basic.status,
      extra_data: {
        centers: d.centers || [],
        users: d.users || [],
        protocol: d.protocol || {}
      }
    };
    
    // 验证必填字段
    if (!trialData.full_name || !trialData.indication || !trialData.sponsor || isNaN(targetEnrollment)) {
      CTMS.showToast('请完整填写带有星号的必填字段', 'error');
      return;
    }
    
    if (targetEnrollment <= 0) {
      CTMS.showToast('目标入组例数必须大于0', 'error');
      return;
    }
    
    try {
      // 1. 先保存至本地系统
      await API.trials.update(trialId, trialData);
      CTMS.saveEditTrialExtraData();

      // 2. 准备 IWRS 同步数据
      const hospitalList = (d.centers || []).map(c => ({
          hospitalName: c.name || "",
          hospitalCode: c.code || "",
          projectLeader: c.pi || ""
      }));

      // ==========================================
      // 从系统全局用户列表 (CTMS_DATA.users) 中查找用户的真实手机号
      // ==========================================
      const getRealPhoneByUserName = (userName) => {
          if (!userName) return "";
          // 在系统用户列表中查找匹配的名字或用户名
          const foundUser = (CTMS_DATA.users || []).find(user => 
              user.name === userName || 
              user.username === userName || 
              user.full_name === userName
          );
          return foundUser ? (foundUser.phone || foundUser.mobile || "") : "";
      };

      const userInfoList = (d.users || []).map(u => {
          const userName = u.name || "";
          // 优先使用当前表单中的 phone，如果没有，则去系统数据库(CTMS_DATA)中查他的真实手机号
          let realPhone = u.phone || getRealPhoneByUserName(userName);
          // 如果系统里也没有记录他的手机号，最后才用 13800000000 兜底，防止 EDC 报错
          realPhone = realPhone || "13800000000";

          return {
              keyword: realPhone, 
              userName: userName,
              hospitalCode: "",
              userTag: u.role || ""
          };
      });

      const payload = {
          project: {
              ctmsProjectId: trialId,
              projectNumber: d.basic.trial_no || trialId,
              projectName: trialData.full_name,
              projectStatus: trialData.status,
              projectType: trialData.phase,
              bidCompany: trialData.sponsor,
              projectSystem: "5"
          },
          projectHospitalList: hospitalList,
          projectUserInfoList: userInfoList
      };

      const targetUrl = "https://syncsim-test.jdhhealth.cn/rws/rwsProject/saveRwsProjectAll";
      
      // 恢复为动态获取当前系统登录用户的 Token
      let userToken = window.API?.token?.getAccessToken() || localStorage.getItem('access_token') || "";
      // 按照要求，直接使用原始的 token 字符串，绝对不加 Bearer 前缀
      if (userToken.toLowerCase().startsWith('bearer ')) {
          userToken = userToken.substring(7).trim();
      }
      const finalToken = userToken;

      console.log("========== 完整调用接口信息概览 ==========");
      console.log("1. 目标 URL: " + targetUrl);
      console.log("2. 请求方法: POST");
      console.log("3. 请求标头 (Headers): ");
      console.log("   - Content-Type: application/json");
      console.log("   - Authorization: " + (finalToken || "缺失"));
      console.log("4. 请求载荷 (Payload): " + JSON.stringify(payload));
      console.log("=======================================");

      if (finalToken) {
          try {
              const response = await fetch(targetUrl, {
                  method: "POST",
                  headers: {
                      "Content-Type": "application/json",
                      "Authorization": finalToken
                  },
                  body: JSON.stringify(payload)
              });
              const resData = await response.json();
              if (resData && String(resData.code) === "1") {
                  CTMS.showToast('修改已保存，并成功同步至EDC！', 'success');
              } else {
                  CTMS.showToast('修改已保存，但同步至EDC失败', 'warning');
                  console.warn("EDC sync response:", resData);
              }
          } catch (syncErr) {
              console.error('同步至EDC网络异常:', syncErr);
              CTMS.showToast('修改已保存，但同步EDC时发生网络异常', 'warning');
          }
      } else {
          CTMS.showToast('修改已保存！(未同步至EDC：缺少凭证)', 'success');
      }

      CTMS.closeModal();
      CTMS.navigate('trial-detail', { trialId: trialId });
    } catch (error) {
      console.error('更新试验失败:', error);
      CTMS.showToast(error.message || '更新失败，请重试', 'error');
    }
  };

  // ===== 试验详情 =====
PAGES['trial-detail'] = function(params) {
  const targetTrialId = params.trialId || (CTMS_DATA.trials && CTMS_DATA.trials.length > 0 ? CTMS_DATA.trials[0].id : 'CT2025001');
  const t = CTMS_DATA.trials.find(x => x.id === targetTrialId || x.apiId === (params.trialApiId || '') || x.apiId === targetTrialId) || getTrialById(targetTrialId);
  if (!t) {
    document.getElementById('main-content').innerHTML = '<div class="empty-state"><div class="empty-icon">📂</div><p>未找到该试验项目，请先创建</p></div>';
    return;
  }
  const editTrialId = params.trialApiId || t.apiId || params.trialId;
  const patients = getPatientsByTrial(t.id);
  const milestones = CTMS_DATA.milestones.filter(m=>m.trialId===t.id);
  const saes = CTMS_DATA.saeEvents.filter(s=>s.trialId===t.id);
  const currentGroup = params.group === 'center' ? 'center' : 'trial';
  const navTrialId = params.trialId || t.id;
  const navTrialApiId = editTrialId || '';
  const extras = loadEditTrialExtraData(t); // Changed from { trial_no: t.id, id: editTrialId } to pass the full trial object t so extra_data is available
  const centerNames = Array.from(new Set([
    ...(extras.centers || []).map(c => c.name).filter(Boolean),
    ...patients.map(p => p.center).filter(c => c && c !== '-')
  ]));
  const selectedCenter = currentGroup === 'center'
    ? (decodeURIComponent(params.center || '') || centerNames[0] || '')
    : '';
  const scopedPatients = (currentGroup === 'center' && selectedCenter)
    ? patients.filter(p => p.center === selectedCenter)
    : patients;
  const patientCenterMap = {};
  patients.forEach(p => {
    patientCenterMap[p.id] = p.center || '';
  });
  const scopedSaes = (currentGroup === 'center' && selectedCenter)
    ? saes.filter(s => patientCenterMap[s.patientId] === selectedCenter)
    : saes;
  const docCenterMap = safeReadLocalMap('ctms_document_center_map');
  const scopedDocuments = (CTMS_DATA.documents || []).filter(d => {
    if (d.trialId !== t.id) return false;
    if (currentGroup !== 'center') return true;
    const docCenter = d.centerName || d.siteName || docCenterMap[d.id] || '';
    return docCenter === selectedCenter;
  });
  const scopedMilestones = currentGroup === 'center'
    ? loadCenterMilestones(t.id, selectedCenter)
    : milestones;
  const selectedCenterTarget = ((extras.centers || []).find(c => c.name === selectedCenter) || {}).target || 0;
  const displayTarget = currentGroup === 'center'
    ? (selectedCenterTarget > 0 ? selectedCenterTarget : Math.max(scopedPatients.length, 1))
    : (t.targetPatients || 0);
  const displayEnrolled = scopedPatients.filter(p => p.status === 'enrolled').length;
  const displayProgress = displayTarget > 0 ? Math.min(100, Math.round(displayEnrolled / displayTarget * 100)) : 0;
  const trialQcCount = CTMS_DATA.qcRecords.filter(q => q.trialId === t.id).length;
  const projectGroupClass = currentGroup === 'trial' ? 'btn-primary' : 'btn-secondary';
  const centerGroupClass = currentGroup === 'center' ? 'btn-primary' : 'btn-secondary';

  document.getElementById('main-content').innerHTML = `
    <div class="page-section">
      <div class="flex-center gap-8 mb-16">
        <button class="btn btn-secondary btn-sm" onclick="CTMS.navigate('trials')">← 返回列表</button>
        <span class="badge badge-blue">${CTMS.getPhaseName(t.phase)}</span>
        <span class="badge ${getStatusBadge(t.status)}">${getStatusLabel(t.status)}</span>
        <div style="flex:1"></div>
        <button class="btn btn-secondary btn-sm">📤 导出报告</button>
        <button class="btn btn-primary btn-sm" onclick="CTMS.editTrial('${editTrialId}')">✏️ 编辑信息</button>
      </div>

      <!-- 基本信息 -->
      <div class="card mb-16">
        <div class="card-body">
          <div style="font-size:18px;font-weight:700;color:var(--gray-900);margin-bottom:12px">${t.name}</div>
          <div class="grid3" style="gap:8px">
            <div><span class="text-muted">试验编号：</span><strong>${t.id}</strong></div>
            <div><span class="text-muted">申办方：</span><strong>${t.sponsor}</strong></div>
            <div><span class="text-muted">适应症：</span><strong>${t.indication}</strong></div>
            <div><span class="text-muted">研究药物：</span><strong>${t.drugName}</strong></div>
            <div><span class="text-muted">主要研究者：</span><strong>${t.pi}</strong></div>
            <div><span class="text-muted">启动日期：</span><strong>${t.startDate}</strong></div>
            <div><span class="text-muted">目标入组：</span><strong>${t.targetPatients} 例</strong></div>
          </div>
        </div>
      </div>

      <!-- 进度统计 -->
      <div class="stats-grid" style="grid-template-columns:repeat(5,1fr)">
        <div class="stat-card"><div class="stat-icon green">👥</div><div class="stat-info"><div class="stat-value">${displayEnrolled}</div><div class="stat-label">已入组</div></div></div>
        <div class="stat-card"><div class="stat-icon blue">🔍</div><div class="stat-info"><div class="stat-value">${scopedPatients.filter(p=>p.status==='screening').length}</div><div class="stat-label">筛选中</div></div></div>
        <div class="stat-card"><div class="stat-icon red">❌</div><div class="stat-info"><div class="stat-value">${scopedPatients.filter(p=>p.status==='screen_fail').length}</div><div class="stat-label">筛选失败</div></div></div>
        <div class="stat-card"><div class="stat-icon yellow">⚠️</div><div class="stat-info"><div class="stat-value">${scopedSaes.length}</div><div class="stat-label">SAE报告</div></div></div>
        <div class="stat-card"><div class="stat-icon purple">✅</div><div class="stat-info"><div class="stat-value">${trialQcCount}</div><div class="stat-label">监查次数</div></div></div>
      </div>

      <div class="flex-center gap-8 mb-8" style="justify-content:flex-start;margin-top:12px">
        <button class="btn ${projectGroupClass} btn-sm" onclick="CTMS.navigate('trial-detail',{trialId:'${navTrialId}',trialApiId:'${navTrialApiId}',group:'trial',activeTab:'tab-overview'})">试验项目组</button>
        <button class="btn ${centerGroupClass} btn-sm" onclick="CTMS.navigate('trial-detail',{trialId:'${navTrialId}',trialApiId:'${navTrialApiId}',group:'center',center:'${encodeURIComponent(selectedCenter)}',activeTab:'tab-overview'})">中心组</button>
      </div>
      ${currentGroup === 'center' ? `
      <div class="form-row" style="margin-bottom:8px">
        <div class="form-group" style="max-width:360px">
          <label class="form-label">中心选择</label>
          <select class="form-select" onchange="CTMS.navigate('trial-detail',{trialId:'${navTrialId}',trialApiId:'${navTrialApiId}',group:'center',center:encodeURIComponent(this.value),activeTab:'tab-overview'})">
            ${centerNames.length === 0 ? '<option value="">暂无中心</option>' : centerNames.map(c => `<option value="${c}" ${c === selectedCenter ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
        </div>
      </div>
      ` : ''}

      <div class="tabs">
        <div class="tab-item active" onclick="switchTab(this,'tab-overview')">项目概况</div>
        <div class="tab-item" onclick="switchTab(this,'tab-milestones')">里程碑</div>
        <div class="tab-item" onclick="switchTab(this,'tab-patients')">受试者(${scopedPatients.length})</div>
        <div class="tab-item" onclick="switchTab(this,'tab-sae')">SAE(${scopedSaes.length})</div>
        <div class="tab-item" onclick="switchTab(this,'tab-qc')">质控记录</div>
        <div class="tab-item" onclick="switchTab(this,'tab-files')">资料归档</div>
        ${currentGroup === 'center' ? `<div class="tab-item" onclick="switchTab(this,'tab-remote-subjects'); loadRemoteSubjects('${t.trial_code || ''}', '${t.id}', '${selectedCenter}')">受试者信息</div>` : ''}
      </div>

      <!-- 项目概况 -->
      <div id="tab-overview" class="tab-content active">
        <div class="grid1">
          <div class="card">
            <div class="card-header"><div class="card-title">📊 入组进度</div></div>
            <div class="card-body">
              <div class="flex-between mb-8">
                <span style="font-size:28px;font-weight:700;color:var(--primary)">${displayProgress}%</span>
                <div style="text-align:right"><div style="font-size:20px;font-weight:700">${displayEnrolled}/${displayTarget}</div><div class="text-muted" style="font-size:12px">已入组/目标</div></div>
              </div>
              <div class="progress-bar" style="height:10px"><div class="progress-fill blue" style="width:${displayProgress}%"></div></div>
              <canvas id="visitChart" width="350" height="140" style="margin-top:16px"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 里程碑 -->
      <div id="tab-milestones" class="tab-content">
        <div class="card">
          <div class="card-header"><div class="card-title">🎯 项目里程碑</div><button class="btn btn-sm btn-primary" onclick="CTMS.showMilestoneModal('${editTrialId}', '${t.id}', '${currentGroup === 'center' ? selectedCenter : ''}')">＋ 添加里程碑</button></div>
          <div class="card-body">
            <div id="milestone-timeline" class="timeline">
              ${currentGroup === 'center' ? renderCenterMilestoneTimelineItems(scopedMilestones, editTrialId, t.id, selectedCenter) : renderMilestoneTimelineItems(scopedMilestones, editTrialId)}
            </div>
          </div>
        </div>
      </div>

      <!-- 受试者 -->
      <div id="tab-patients" class="tab-content">
        <div class="card">
          <div class="card-header"><div class="card-title">👥 受试者列表</div>
            <button class="btn btn-sm btn-primary" onclick="CTMS.navigate('patients')">管理受试者</button>
          </div>
          <div class="card-body table-container">
            <table>
              <thead><tr><th>受试者ID</th><th>年龄/性别</th><th>分配组别</th><th>状态</th><th>知情同意</th><th>入组日期</th><th>访视次数</th><th>下次访视</th></tr></thead>
              <tbody>
                ${scopedPatients.map(p=>`<tr>
                  <td><span class="text-primary" style="cursor:pointer;font-weight:500" onclick="CTMS.showPatientDetail('${p.id}')">${p.id}</span></td>
                  <td>${p.age}岁/${p.gender}</td>
                  <td>${p.arm}</td>
                  <td><span class="badge ${getStatusBadge(p.status)}">${getStatusLabel(p.status)}</span></td>
                  <td>${p.icfSigned?'<span class="badge badge-green">✅ 已签署</span>':'<span class="badge badge-yellow">⏳ 待签署</span>'}</td>
                  <td>${p.enrollDate||'-'}</td>
                  <td>${p.visitCount}</td>
                  <td>${p.nextVisit||'-'}</td>
                </tr>`).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- SAE -->
      <div id="tab-sae" class="tab-content">
        <div class="card">
          <div class="card-header"><div class="card-title">⚠️ SAE 不良事件报告</div>
            <button class="btn btn-sm btn-primary" onclick="CTMS.showSAEModal('${editTrialId}','${t.id}','${currentGroup === 'center' ? selectedCenter : ''}')">＋ 新增SAE</button>
          </div>
          <div class="card-body table-container">
            <table>
              <thead><tr><th>报告编号</th><th>受试者ID</th><th>事件名称</th><th>严重程度</th><th>与试验药关系</th><th>首次报告日期</th><th>状态</th><th>报告类型</th><th>操作</th></tr></thead>
              <tbody id="trial-sae-tbody">
                ${renderTrialSAERows(scopedSaes)}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 质控 -->
      <div id="tab-qc" class="tab-content">
        <div class="card">
          <div class="card-header"><div class="card-title">✅ 质量控制记录</div>
            <button class="btn btn-sm btn-primary" onclick="CTMS.showQCModal('${editTrialId}', '${t.id}', '${currentGroup === 'center' ? selectedCenter : ''}')">＋ 新增监查</button>
          </div>
          <div class="card-body table-container">
            <table>
              <thead><tr><th>记录编号</th><th>监查类型</th><th>监查日期</th><th>CRA</th><th>发现问题数</th><th>已关闭</th><th>状态</th><th style="text-align:right">操作</th></tr></thead>
              <tbody id="trial-qc-tbody">
                <tr><td colspan="8" style="text-align:center;color:var(--gray-500)">正在加载...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 资料归档 -->
      <div id="tab-files" class="tab-content">
        <div class="card">
          <div class="card-header"><div class="card-title">🗄️ eTMF 文档归档</div><button class="btn btn-sm btn-primary" onclick="CTMS.showEtmfUploadModal('${editTrialId}', '${t.id}', '${currentGroup === 'center' ? selectedCenter : ''}')">＋ 上传文件</button></div>
          <div class="card-body">
            ${['注册资料', '伦理文件', '方案文件', '知情同意书', '监查报告', '安全性报告', 'SOP文件', '合同文件', '数据管理计划', '关闭报告'].map((cat,i)=>{
              const docs = scopedDocuments.filter(d => (d.docType === cat || (!d.docType && cat === '注册资料')));
              return `
              <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--gray-100)">
                <div style="display:flex;align-items:center;gap:10px">
                  <span style="font-size:18px">📁</span>
                  <div>
                    <div style="font-size:13px;font-weight:500">${cat}</div>
                    <div class="text-muted" style="font-size:11px">${docs.length} 个文件</div>
                  </div>
                </div>
                <div style="display:flex;align-items:center;gap:8px">
                  <span class="badge ${docs.length > 0 ? 'badge-green' : 'badge-yellow'}">${docs.length > 0 ? '合规' : '待上传'}</span>
                  <button class="btn btn-sm btn-secondary" onclick="CTMS.showEtmfCategoryFiles('${t.id}', '${cat}', '${currentGroup === 'center' ? selectedCenter : ''}')">查看</button>
                </div>
              </div>
            `}).join('')}
          </div>
        </div>
      </div>

      <!-- 受试者信息(远程嵌入) -->
      ${currentGroup === 'center' ? `
      <div id="tab-remote-subjects" class="tab-content">
        <div class="card" style="height: calc(100vh - 250px); display: flex; flex-direction: column;">
          <div class="card-header"><div class="card-title">🌐 受试者信息 (外部系统)</div></div>
          <div class="card-body" style="flex: 1; padding: 0; position: relative;" id="remote-subjects-container">
            <div id="remote-subjects-loading" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.8); z-index: 10;">
              <div style="text-align: center; color: var(--gray-500);">
                <div style="font-size: 24px; margin-bottom: 8px;">⏳</div>
                <div>正在加载远程受试者数据...</div>
              </div>
            </div>
            <iframe id="remote-subjects-iframe" style="width: 100%; height: 100%; border: none;" allowfullscreen></iframe>
          </div>
        </div>
      </div>
      ` : ''}
    </div>
  `;
  CTMS.refreshMilestones(editTrialId, currentGroup === 'center' ? selectedCenter : '', t.id);
  CTMS.refreshTrialSAE(editTrialId, t.id, currentGroup === 'center' ? selectedCenter : '', patientCenterMap);
  CTMS.refreshTrialQC(editTrialId, t.id, currentGroup === 'center' ? selectedCenter : '');
  if (params.activeTab && params.activeTab !== 'tab-overview') {
    const tabEl = document.querySelector(`.tab-item[onclick*="${params.activeTab}"]`);
    if (tabEl) switchTab(tabEl, params.activeTab);
  }
  setTimeout(()=>drawTrialCharts(t, scopedPatients), 100);
};

function mapAESeverityLabel(severity) {
  const m = {
    GRADE_1: '1级',
    GRADE_2: '2级',
    GRADE_3: '3级',
    GRADE_4: '4级',
    GRADE_5: '5级',
  };
  return m[severity] || severity || '-';
}

function mapAERelatednessLabel(relatedness) {
  const m = {
    DEFINITE: '肯定相关',
    PROBABLE: '很可能相关',
    POSSIBLE: '可能相关',
    UNLIKELY: '可能不相关',
    UNRELATED: '肯定不相关',
    UNKNOWN: '无法评价',
  };
  return m[relatedness] || relatedness || '-';
}

function renderTrialSAERows(saes) {
  if (!saes || saes.length === 0) {
    return '<tr><td colspan="8" style="text-align:center;color:var(--gray-500)">暂无SAE记录</td></tr>';
  }
  return saes.map(s => {
    const statusMap = {
      'INITIAL': '提交中',
      'PENDING': '提交中',
      'RESOLVED': '已完成',
      'COMPLETED': '已完成',
      'FOLLOW_UP': '随访中'
    };
    const displayStatus = statusMap[s.status] || s.status;
    const isResolved = displayStatus === '已完成' || displayStatus === '已恢复' || displayStatus === 'RECOVERED';
    return `
    <tr>
      <td>${s.id || '-'}</td><td>${s.patientId || '-'}</td><td><strong>${s.eventName || '-'}</strong></td>
      <td><span class="badge ${String(s.severity || '').includes('3') || String(s.severity || '').includes('4') || String(s.severity || '').includes('5') ? 'badge-red':'badge-yellow'}">${s.severity || '-'}</span></td>
      <td>${s.causality || '-'}</td><td>${s.reportDate || '-'}</td>
      <td><span class="badge ${isResolved ? 'badge-green':'badge-yellow'}">${displayStatus || '-'}</span></td>
      <td>${s.reportType || '-'}</td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="CTMS.viewSAEDetail('${s.id}')">查看</button>
      </td>
    </tr>
  `}).join('');
}

CTMS.refreshTrialSAE = async function(trialApiId, trialNo, centerName = '', patientCenterMap = null) {
  if (!trialApiId) return;
  try {
    const res = await API.ae.list({ trial_id: trialApiId, page: 1, page_size: 100 });
    const items = (res && res.items) ? res.items : [];
    const patientMap = {};
    (CTMS_DATA.patients || []).forEach(p => {
      if (p.apiId) patientMap[p.apiId] = p.id;
    });
    const mapped = items.map(a => ({
      id: a.ae_no || a.id,
      trialId: trialNo,
      patientId: patientMap[a.patient_id] || a.patient_id || '-',
      eventName: a.description || '-',
      severity: mapAESeverityLabel(a.severity),
      reportDate: a.created_at || a.onset_date || '-',
      status: a.outcome || a.report_status || '随访中',
      causality: mapAERelatednessLabel(a.relatedness),
      reportType: a.report_status === 'INITIAL' ? '首次报告' : '跟踪报告',
    }));
    CTMS_DATA.saeEvents = (CTMS_DATA.saeEvents || []).filter(x => x.trialId !== trialNo).concat(mapped);
    const centerMap = patientCenterMap || {};
    const scoped = centerName
      ? mapped.filter(x => centerMap[x.patientId] === centerName)
      : mapped;
    const tbody = document.getElementById('trial-sae-tbody');
    if (tbody) tbody.innerHTML = renderTrialSAERows(scoped);
  } catch (error) {
    const tbody = document.getElementById('trial-sae-tbody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--danger)">SAE加载失败</td></tr>';
    CTMS.showToast(error.message || 'SAE加载失败', 'error');
  }
};

CTMS.showQCModal = function(trialApiId, trialNo, centerName = '') {
  CTMS.showModal('新增监查记录', `
    <div class="form-row">
      <div class="form-group"><label class="form-label required">监查类型</label>
        <select id="qc-visit-type" class="form-select">
          <option value="常规监查">常规监查</option>
          <option value="触发性监查">触发性监查</option>
          <option value="启动监查">启动监查</option>
          <option value="关中心监查">关中心监查</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label required">监查日期</label>
        <input id="qc-visit-date" class="form-input" type="date" value="${new Date().toISOString().slice(0,10)}">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label required">总体评价</label>
        <select id="qc-overall-rating" class="form-select">
          <option value="GREEN">合规 (GREEN)</option>
          <option value="YELLOW">需关注 (YELLOW)</option>
          <option value="RED">严重问题 (RED)</option>
        </select>
      </div>
    </div>
    ${centerName ? `<div class="alert alert-info">当前中心：${centerName}</div>` : ''}
  `, `<button class="btn btn-secondary" onclick="CTMS.closeModal()">取消</button><button class="btn btn-primary" onclick="CTMS.submitQC('${trialApiId}', '${trialNo}', '${centerName || ''}')">提交记录</button>`);
};

CTMS.submitQC = async function(trialApiId, trialNo, centerName = '') {
  const visitType = document.getElementById('qc-visit-type')?.value;
  const visitDate = document.getElementById('qc-visit-date')?.value;
  const overallRating = document.getElementById('qc-overall-rating')?.value;

  if (!visitType || !visitDate) {
    CTMS.showToast('请完整填写带有星号的必填项', 'error');
    return;
  }

  try {
    // 假设 site_id 目前非强制，或者我们可以传入一个 mock uuid 或者从中心列表里取
    // 暂时传入试用项目的 site_id 或者空 (如果后端允许为空的话，但目前模型要求 site_id)
    // 根据 models.py, MonitoringReport 的 site_id 是可空的? 实际上 MonitoringReportCreate 里 site_id 是必填 UUID。
    // 我们需要先获取一个 site_id。为了简便，我们从当前试验中随机获取一个，或者直接硬编码一个。
    // 为了稳妥，如果 API.monitoring 真的强制需要，我们需要先拿到中心列表。
    // 我们可以直接在代码中通过 API 或者给个全零 UUID。
    let siteId = '00000000-0000-0000-0000-000000000000'; // 暂时代替
    
    // 我们先尝试获取任意一个 site
    try {
      const sites = await API.trials.listSites(trialApiId);
      if (sites && sites.items && sites.items.length > 0) {
        const matched = centerName ? sites.items.find(s => (s.name || s.site_name || '') === centerName) : null;
        siteId = (matched && matched.id) ? matched.id : sites.items[0].id;
      }
    } catch (e) {
      console.warn("Could not fetch sites, using fallback uuid");
    }

    await API.monitoring.createReport({
      trial_id: trialApiId,
      site_id: siteId === '00000000-0000-0000-0000-000000000000' ? null : siteId,
      visit_type: visitType,
      visit_date: visitDate,
      overall_rating: overallRating,
      findings: [],
      actions: []
    });

    CTMS.showToast('监查记录添加成功', 'success');
    CTMS.closeModal();
    CTMS.refreshTrialQC(trialApiId, trialNo, centerName);
  } catch (error) {
    CTMS.showToast(error.message || '监查记录添加失败', 'error');
  }
};

CTMS.refreshTrialQC = async function(trialApiId, trialNo, centerName = '') {
  if (!trialApiId) return;
  try {
    const res = await API.monitoring.listReports({ trial_id: trialApiId, page: 1, page_size: 100 });
    const items = (res && res.items) ? res.items : [];
    
    const tbody = document.getElementById('trial-qc-tbody');
    if (!tbody) return;

    let scopedItems = items;
    if (centerName) {
      const withCenter = items.filter(q => {
        const reportCenter = q.site_name || q.siteName || q.center || q.site?.name || '';
        return reportCenter === centerName;
      });
      // 如果后端暂未返回中心字段，则回退显示项目级数据，避免误判为空
      if (withCenter.length > 0) scopedItems = withCenter;
    }
    
    if (scopedItems.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--gray-500)">暂无监查记录</td></tr>';
      return;
    }
    
    tbody.innerHTML = scopedItems.map(q => {
      const findingsCount = q.findings ? q.findings.length : 0;
      const closedCount = (q.findings || []).filter(f => f.status === 'CLOSED').length;
      return `<tr>
        <td>${q.report_no || q.id}</td>
        <td>${q.visit_type || '-'}</td>
        <td>${q.visit_date ? CTMS.formatDateTime(q.visit_date) : '-'}</td>
        <td>CRA</td>
        <td><span class="badge ${findingsCount > 0 ? 'badge-yellow' : 'badge-green'}">${findingsCount}</span></td>
        <td>${closedCount}</td>
        <td><span class="badge badge-green">${q.status === 'SUBMITTED' ? '已提交' : (q.status || '-')}</span></td>
        <td style="text-align:right">
          <button class="btn btn-sm btn-danger" onclick="CTMS.deleteQC('${trialApiId}', '${trialNo}', '${q.id}', '${centerName || ''}')" title="删除">🗑️</button>
        </td>
      </tr>`;
    }).join('');
  } catch (error) {
    const tbody = document.getElementById('trial-qc-tbody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--danger)">监查记录加载失败</td></tr>';
    CTMS.showToast(error.message || '监查记录加载失败', 'error');
  }
};

CTMS.deleteQC = async function(trialApiId, trialNo, reportId, centerName = '') {
  if (!confirm('⚠️ 确定要删除该监查记录吗？此操作不可恢复。')) return;
  try {
    await API.monitoring.deleteReport(reportId);
    CTMS.showToast('监查记录已成功删除', 'success');
    CTMS.refreshTrialQC(trialApiId, trialNo, centerName);
  } catch (error) {
    CTMS.showToast(error.message || '删除失败', 'error');
  }
};

function renderMilestoneTimelineItems(milestones, trialApiId) {
  if (!milestones || milestones.length === 0) {
    return '<div class="empty-state"><div class="empty-icon">🎯</div><p>暂无里程碑，请新增</p></div>';
  }
  return milestones.map(m => `
    <div class="timeline-item">
      <div class="timeline-dot ${m.status==='done'?'green':m.status==='pending'?'gray':''}"></div>
      <div class="timeline-date">${m.doneDate?'完成：'+m.doneDate:'计划：'+(m.dueDate || '-')}</div>
      <div class="flex-between">
        <div class="timeline-content">${m.name}</div>
        <span class="badge ${m.status==='done'?'badge-green':'badge-yellow'}">${m.status==='done'?'已完成':'待完成'}</span>
      </div>
      <div class="timeline-sub">${m.type ? `类型：${m.type}` : ''}${m.assignee ? ` · 负责人：${m.assignee}` : ''}</div>
      <div style="margin-top:8px">
        <button class="btn btn-sm ${m.status==='done'?'btn-secondary':'btn-primary'}" onclick="CTMS.toggleMilestoneStatus('${trialApiId}','${m.id}','${m.status}')">${m.status==='done'?'恢复待完成':'标记完成'}</button>
      </div>
    </div>
  `).join('');
}

function renderCenterMilestoneTimelineItems(milestones, trialApiId, trialNo, centerName) {
  if (!milestones || milestones.length === 0) {
    return '<div class="empty-state"><div class="empty-icon">🎯</div><p>该中心暂无里程碑，请新增</p></div>';
  }
  return milestones.map(m => `
    <div class="timeline-item">
      <div class="timeline-dot ${m.status==='done'?'green':m.status==='pending'?'gray':''}"></div>
      <div class="timeline-date">${m.doneDate?'完成：'+m.doneDate:'计划：'+(m.dueDate || '-')}</div>
      <div class="flex-between">
        <div class="timeline-content">${m.name}</div>
        <span class="badge ${m.status==='done'?'badge-green':'badge-yellow'}">${m.status==='done'?'已完成':'待完成'}</span>
      </div>
      <div class="timeline-sub">${m.type ? `类型：${m.type}` : ''}${m.assignee ? ` · 负责人：${m.assignee}` : ''}</div>
      <div style="margin-top:8px">
        <button class="btn btn-sm ${m.status==='done'?'btn-secondary':'btn-primary'}" onclick="CTMS.toggleMilestoneStatus('${trialApiId}','${m.id}','${m.status}','${trialNo || ''}','${centerName || ''}')">${m.status==='done'?'恢复待完成':'标记完成'}</button>
      </div>
    </div>
  `).join('');
}

function normalizeMilestones(rawItems) {
  const typeMap = {
    'STARTUP': '启动',
    'ENROLLMENT': '入组',
    'MONITORING': '监查',
    'VISIT': '访视',
    'DATA_EVALUATION': '数据评估',
    'DATA_MANAGEMENT': '数据管理',
    'STATISTICS': '统计',
    'COMPLETION': '完成',
    'DATA_LOCK': '数据库锁定',
    'CLOSEOUT': '结题'
  };

  return (rawItems || []).map(m => ({
    id: m.id,
    name: m.name || '未命名里程碑',
    type: typeMap[m.milestone_type] || m.milestone_type || '',
    dueDate: m.planned_date || null,
    doneDate: m.actual_date || null,
    assignee: m.owner_name || '',
    status: m.status === 'DONE' ? 'done' : 'pending',
    notes: m.notes || '',
  }));
}

function getCenterMilestoneStorageKey(trialNo, centerName) {
  return `${trialNo || ''}::${centerName || ''}`;
}

function loadCenterMilestones(trialNo, centerName) {
  if (!trialNo || !centerName) return [];
  const map = safeReadLocalMap('ctms_trial_center_milestones_map');
  const key = getCenterMilestoneStorageKey(trialNo, centerName);
  return Array.isArray(map[key]) ? map[key] : [];
}

function saveCenterMilestones(trialNo, centerName, milestones) {
  if (!trialNo || !centerName) return;
  const map = safeReadLocalMap('ctms_trial_center_milestones_map');
  const key = getCenterMilestoneStorageKey(trialNo, centerName);
  map[key] = Array.isArray(milestones) ? milestones : [];
  safeWriteLocalMap('ctms_trial_center_milestones_map', map);
}

async function resolveTrialApiId(trialApiId, trialNo) {
  if (trialApiId) return trialApiId;
  const local = (CTMS_DATA.trials || []).find(x => x.id === trialNo);
  if (local && local.apiId) return local.apiId;
  try {
    const res = await API.trials.list({ page: 1, page_size: 20, keyword: trialNo || '' });
    const items = (res && res.items) ? res.items : [];
    const hit = items.find(x => x.trial_no === trialNo) || items[0];
    return hit ? String(hit.id) : '';
  } catch (e) {
    return '';
  }
}

CTMS.refreshMilestones = async function(trialApiId, centerName = '', trialNo = '') {
  if (centerName && trialNo) {
    const panel = document.getElementById('milestone-timeline');
    if (!panel) return;
    const localMilestones = loadCenterMilestones(trialNo, centerName);
    panel.innerHTML = renderCenterMilestoneTimelineItems(localMilestones, trialApiId, trialNo, centerName);
    return;
  }
  if (!trialApiId) return;
  try {
    const res = await API.trials.getMilestones(trialApiId);
    const milestones = normalizeMilestones(res.data || []);
    const panel = document.getElementById('milestone-timeline');
    if (!panel) return;
    panel.innerHTML = renderMilestoneTimelineItems(milestones, trialApiId);
  } catch (error) {
    const panel = document.getElementById('milestone-timeline');
    if (!panel) return;
    panel.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><p>里程碑加载失败</p></div>';
    CTMS.showToast(error.message || '里程碑加载失败', 'error');
  }
};

CTMS.showMilestoneModal = async function(trialApiId, trialNo, centerName = '') {
  const resolvedTrialApiId = await resolveTrialApiId(trialApiId, trialNo);
  if (!resolvedTrialApiId) {
    CTMS.showToast('试验ID无效，无法新增里程碑', 'error');
    return;
  }
  const modalTitle = centerName ? `新增里程碑 - ${trialNo} / ${centerName}` : `新增里程碑 - ${trialNo}`;
  CTMS.showModal(modalTitle, `
    <div class="form-row col3">
      <div class="form-group">
        <label class="form-label required">里程碑名称</label>
        <input id="ms-name" class="form-input" placeholder="如：首例入组">
      </div>
      <div class="form-group">
        <label class="form-label">里程碑类型</label>
        <select id="ms-type" class="form-select">
          <option value="">请选择</option>
          <option value="STARTUP">启动</option>
          <option value="ENROLLMENT">入组</option>
          <option value="MONITORING">监查</option>
          <option value="VISIT">访视</option>
          <option value="DATA_EVALUATION">数据评估</option>
          <option value="DATA_MANAGEMENT">数据管理</option>
          <option value="STATISTICS">统计</option>
          <option value="COMPLETION">完成</option>
          <option value="DATA_LOCK">数据库锁定</option>
          <option value="CLOSEOUT">结题</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">计划日期</label>
        <input id="ms-planned-date" class="form-input" type="date">
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">备注</label>
      <textarea id="ms-notes" class="form-textarea" placeholder="里程碑说明"></textarea>
    </div>
  `, `<button class="btn btn-secondary" onclick="CTMS.closeModal()">取消</button><button class="btn btn-primary" onclick="CTMS.createMilestone('${resolvedTrialApiId}','${trialNo || ''}','${centerName || ''}')">创建里程碑</button>`);
};

CTMS.createMilestone = async function(trialApiId, trialNo = '', centerName = '') {
  const resolvedTrialApiId = await resolveTrialApiId(trialApiId, trialNo);
  if (!resolvedTrialApiId) {
    CTMS.showToast('试验ID无效，无法创建里程碑', 'error');
    return;
  }
  const payload = {
    name: document.getElementById('ms-name')?.value?.trim(),
    milestone_type: document.getElementById('ms-type')?.value || null,
    planned_date: document.getElementById('ms-planned-date')?.value || null,
    notes: document.getElementById('ms-notes')?.value?.trim() || null,
  };
  
  if (!payload.name) {
    CTMS.showToast('请输入里程碑名称', 'error');
    return;
  }
  
  if (!payload.milestone_type) {
    CTMS.showToast('请选择里程碑类型', 'error');
    return;
  }
  
  if (centerName && trialNo) {
    const localMilestones = loadCenterMilestones(trialNo, centerName);
    localMilestones.push({
      id: `local-ms-${Date.now()}`,
      name: payload.name,
      type: ({
        STARTUP: '启动', ENROLLMENT: '入组', MONITORING: '监查', VISIT: '访视',
        DATA_EVALUATION: '数据评估', DATA_MANAGEMENT: '数据管理', STATISTICS: '统计',
        COMPLETION: '完成', DATA_LOCK: '数据库锁定', CLOSEOUT: '结题'
      })[payload.milestone_type] || payload.milestone_type,
      dueDate: payload.planned_date || null,
      doneDate: null,
      assignee: '',
      status: 'pending',
      notes: payload.notes || '',
    });
    saveCenterMilestones(trialNo, centerName, localMilestones);
    CTMS.closeModal();
    CTMS.showToast('中心里程碑创建成功', 'success');
    await CTMS.refreshMilestones(resolvedTrialApiId, centerName, trialNo);
    return;
  }

  try {
    await API.trials.createMilestone(resolvedTrialApiId, payload);
    CTMS.closeModal();
    CTMS.showToast('里程碑创建成功', 'success');
    await CTMS.refreshMilestones(resolvedTrialApiId);
  } catch (error) {
    CTMS.showToast(error.message || '里程碑创建失败', 'error');
  }
};

CTMS.toggleMilestoneStatus = async function(trialApiId, milestoneId, currentStatus, trialNo = '', centerName = '') {
  const resolvedTrialApiId = await resolveTrialApiId(trialApiId, '');
  if (!resolvedTrialApiId) {
    CTMS.showToast('试验ID无效，无法更新里程碑状态', 'error');
    return;
  }
  if (centerName && trialNo) {
    const localMilestones = loadCenterMilestones(trialNo, centerName);
    const next = localMilestones.map(m => {
      if (String(m.id) !== String(milestoneId)) return m;
      if (currentStatus === 'done') {
        return { ...m, status: 'pending', doneDate: null };
      }
      return { ...m, status: 'done', doneDate: new Date().toISOString().slice(0, 10) };
    });
    saveCenterMilestones(trialNo, centerName, next);
    CTMS.showToast(currentStatus === 'done' ? '里程碑已恢复为待完成' : '里程碑已标记完成', 'success');
    await CTMS.refreshMilestones(resolvedTrialApiId, centerName, trialNo);
    return;
  }
  try {
    if (currentStatus === 'done') {
      await API.trials.updateMilestone(resolvedTrialApiId, milestoneId, { status: 'PENDING', actual_date: null });
      CTMS.showToast('里程碑已恢复为待完成', 'success');
    } else {
      await API.trials.updateMilestone(resolvedTrialApiId, milestoneId, { status: 'DONE', actual_date: new Date().toISOString().slice(0, 10) });
      CTMS.showToast('里程碑已标记完成', 'success');
    }
    await CTMS.refreshMilestones(resolvedTrialApiId);
  } catch (error) {
    CTMS.showToast(error.message || '里程碑状态更新失败', 'error');
  }
};

function drawTrialCharts(t, scopedPatients) {
  if (!window.Chart) return;
  const patients = Array.isArray(scopedPatients)
    ? scopedPatients
    : CTMS_DATA.patients.filter(p => p.trialId === t.id);
  const vCtx = document.getElementById('visitChart');
  if (vCtx) {
    new Chart(vCtx, {
      type: 'bar',
      data: {
        labels: ['筛选失败','筛选中','已入组','脱落'],
        datasets: [{ data: [
          patients.filter(p=>p.status==='screen_fail').length,
          patients.filter(p=>p.status==='screening').length,
          patients.filter(p=>p.status==='enrolled').length,
          patients.filter(p=>p.status==='dropout').length,
        ], backgroundColor: ['#ef4444','#3b82f6','#22c55e','#9ca3af'], borderRadius: 4 }]
      },
      options: { responsive: true, plugins: { legend:{display:false} }, scales: { y:{beginAtZero:true}, x:{grid:{display:false}} } }
    });
  }
  const bCtx = document.getElementById('budgetChart');
  if (bCtx) {
    new Chart(bCtx, {
      type: 'doughnut',
      data: {
        labels: ['已支出', '剩余'],
        datasets: [{ data: [t.budgetUsed, t.budget-t.budgetUsed], backgroundColor: ['#1a6fc4','#e5e7eb'], borderWidth: 0 }]
      },
      options: { responsive:true, cutout:'70%', plugins:{legend:{position:'bottom',labels:{font:{size:11}}}} }
    });
  }
}

function switchTab(el, tabId) {
  el.closest('.page-section').querySelectorAll('.tab-item').forEach(t=>t.classList.remove('active'));
  el.closest('.page-section').querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

window.loadRemoteSubjects = function(trialCode, trialId, hospitalName) {
  const iframe = document.getElementById('remote-subjects-iframe');
  const loading = document.getElementById('remote-subjects-loading');
  if (!iframe || !loading) return;

  const token = sessionStorage.getItem('user_token') || '';
  if (!token) {
    loading.innerHTML = '<div style="text-align:center;color:#ef4444;"><div style="font-size:24px;margin-bottom:8px;">⚠️</div><div>缺少用户 Token，请重新登录</div></div>';
    return;
  }
  
  if (!hospitalName) {
    loading.innerHTML = '<div style="text-align:center;color:#f59e0b;"><div style="font-size:24px;margin-bottom:8px;">ℹ️</div><div>请先选择一个中心</div></div>';
    return;
  }

  // Fallback to trial_no (trialId) if trialCode is missing or null in the database
  const finalProjectId = trialCode || trialId;

  // Construct the remote URL using URL and URLSearchParams to ensure proper parameter joining
  const remoteUrlObj = new URL('https://icrpsim.jdhhealth.cn/Back/subject-list/index.html');
  remoteUrlObj.searchParams.append('token', token);
  remoteUrlObj.searchParams.append('projectId', finalProjectId);
  remoteUrlObj.searchParams.append('hospitalName', hospitalName);
  remoteUrlObj.searchParams.append('apiBase', 'https://syncsim-prod.jdhhealth.cn');
  const targetUrl = remoteUrlObj.toString();

  // Show loading state
  loading.style.display = 'flex';
  
  // Set iframe source
  iframe.src = targetUrl;
  
  // Handle iframe load event
  iframe.onload = function() {
    loading.style.display = 'none';
  };
  
  // Handle iframe error fallback (basic timeout since onload might fire even on 404/500 for cross-origin)
  setTimeout(() => {
    if (loading.style.display !== 'none') {
      loading.innerHTML = '<div style="text-align:center;color:#ef4444;"><div style="font-size:24px;margin-bottom:8px;">❌</div><div>加载远程页面超时，请检查网络或刷新重试</div></div>';
    }
  }, 10000);
};
