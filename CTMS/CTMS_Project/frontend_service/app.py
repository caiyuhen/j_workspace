<<<<<<< HEAD
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="CTMS Frontend")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>CTMS 全功能控制台</title>
  <style>
    body{font-family:Arial;margin:0;background:#f5f7fb}
    header{background:#1e40af;color:#fff;padding:12px 18px}
    .container{padding:16px}
    .card{background:#fff;border-radius:8px;padding:12px;margin-bottom:14px}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    input,select,textarea,button{width:100%;padding:8px;margin-top:6px;box-sizing:border-box}
    button{background:#2563eb;color:#fff;border:0;border-radius:6px;cursor:pointer}
    pre{background:#111827;color:#e5e7eb;padding:10px;border-radius:8px;overflow:auto}
  </style>
</head>
<body>
  <header>CTMS 全功能控制台 | <a href="http://127.0.0.1:8001/docs" style="color:#bfdbfe">Project</a> | <a href="http://127.0.0.1:8002/docs" style="color:#bfdbfe">Randomization</a> | <a href="http://127.0.0.1:8003/docs" style="color:#bfdbfe">Audit</a> | <a href="http://127.0.0.1:8004/docs" style="color:#bfdbfe">Patient</a> | <a href="http://127.0.0.1:8005/docs" style="color:#bfdbfe">Validation</a> | <a href="http://127.0.0.1:8006/docs" style="color:#bfdbfe">Monitoring</a> | <a href="http://127.0.0.1:8007/docs" style="color:#bfdbfe">Security</a></header>
  <div class="container">
    <div class="grid">
      <div class="card">
        <h3>项目与随机化开关</h3>
        <input id="proj_name" placeholder="项目名称" value="肺癌III期"/>
        <select id="proj_rand"><option value="true">开启随机化</option><option value="false">关闭随机化</option></select>
        <button onclick="createProject()">创建项目</button>
        <input id="switch_project_id" placeholder="项目ID"/>
        <select id="switch_enabled"><option value="true">切换为开启</option><option value="false">切换为关闭</option></select>
        <button onclick="toggleSwitch()">切换开关</button>
      </div>
      <div class="card">
        <h3>中心与预算</h3>
        <input id="site_project_id" placeholder="项目ID"/>
        <input id="site_name" placeholder="中心名称" value="北京协和医院"/>
        <input id="site_budget" placeholder="预算" value="500000"/>
        <button onclick="createSite()">创建中心</button>
        <button onclick="listSites()">查询中心</button>
        <pre id="site_out"></pre>
      </div>
    </div>
    <div class="grid">
      <div class="card">
        <h3>患者入组与eICF</h3>
        <input id="pat_project_id" placeholder="项目ID"/>
        <input id="pat_name" placeholder="姓名" value="张三"/>
        <input id="pat_age" placeholder="年龄" value="45"/>
        <select id="pat_severity"><option value="low">low</option><option value="medium">medium</option><option value="high">high</option></select>
        <button onclick="enrollPatient()">入组并分组</button>
        <input id="eicf_patient_id" placeholder="患者ID"/>
        <button onclick="signEicf()">签署eICF</button>
        <button onclick="listPatients()">查询患者</button>
      </div>
      <div class="card">
        <h3>数据校验与清洗</h3>
        <textarea id="clean_payload" rows="6">[{"id":1,"value":120},{"id":2,"value":null},{"id":3,"value":1400}]</textarea>
        <button onclick="cleanData()">执行清洗</button>
        <pre id="clean_out"></pre>
      </div>
    </div>
    <div class="grid">
      <div class="card">
        <h3>风险监控</h3>
        <input id="risk_project_id" placeholder="项目ID"/>
        <input id="risk_name" placeholder="指标名" value="enrollment_delay"/>
        <input id="risk_value" placeholder="指标值" value="45"/>
        <input id="risk_threshold" placeholder="阈值" value="30"/>
        <button onclick="addRisk()">提交风险指标</button>
        <button onclick="riskDashboard()">查看风险仪表盘</button>
        <pre id="risk_out"></pre>
      </div>
      <div class="card">
        <h3>权限安全</h3>
        <input id="sec_user" placeholder="用户名" value="cra_user"/>
        <input id="sec_role" placeholder="角色" value="CRA"/>
        <input id="sec_group" placeholder="权限组" value="monitoring"/>
        <button onclick="assignRole()">分配角色</button>
        <button onclick="runSensitive()">执行敏感操作(双因子)</button>
        <button onclick="listUsers()">查询用户</button>
        <pre id="sec_out"></pre>
      </div>
    </div>
    <div class="card">
      <h3>审计日志</h3>
      <button onclick="getAudit()">刷新审计日志</button>
      <pre id="audit_out"></pre>
    </div>
  </div>
  <script>
    async function api(port, path, method, payload){
      const res = await fetch(`http://127.0.0.1:${port}${path}`, {method, headers: {"Content-Type":"application/json"}, body: payload?JSON.stringify(payload):undefined});
      const data = await res.json();
      if(!res.ok){ alert(JSON.stringify(data)); throw new Error(data.detail || "error"); }
      return data;
    }
    async function createProject(){
      const r = await api(8001, "/projects", "POST", {name: proj_name.value, randomization_enabled: proj_rand.value==="true", protocol_reason: "Intervention"});
      switch_project_id.value = r.project_id; site_project_id.value = r.project_id; pat_project_id.value = r.project_id; risk_project_id.value = r.project_id;
      alert("project_id=" + r.project_id);
    }
    async function toggleSwitch(){ await api(8001, `/projects/${switch_project_id.value}/randomization-switch`, "PUT", {enabled: switch_enabled.value==="true", operator_id: "PM-001", operator_ip: "127.0.0.1", signature: "SIG-PM001", mfa_verified: true}); }
    async function createSite(){ site_out.textContent = JSON.stringify(await api(8001, "/sites", "POST", {project_id:Number(site_project_id.value), site_name:site_name.value, planned_budget:Number(site_budget.value)}), null, 2); }
    async function listSites(){ site_out.textContent = JSON.stringify(await api(8001, `/sites?project_id=${site_project_id.value}`, "GET"), null, 2); }
    async function enrollPatient(){ const r = await api(8004, "/patients", "POST", {project_id:Number(pat_project_id.value), name:pat_name.value, age:Number(pat_age.value), severity:pat_severity.value, operator_id:"INV-001", operator_ip:"127.0.0.1", signature:"SIG-INV001", mfa_verified:true}); eicf_patient_id.value = r.patient_id; alert(JSON.stringify(r)); }
    async function signEicf(){ await api(8004, "/patients/eicf-sign", "POST", {patient_id:Number(eicf_patient_id.value), operator_id:"INV-001", operator_ip:"127.0.0.1", signature:"SIG-INV001", mfa_verified:true}); }
    async function listPatients(){ audit_out.textContent = JSON.stringify(await api(8004, `/patients?project_id=${pat_project_id.value}`, "GET"), null, 2); }
    async function cleanData(){ clean_out.textContent = JSON.stringify(await api(8005, "/clean", "POST", {points: JSON.parse(clean_payload.value)}), null, 2); }
    async function addRisk(){ risk_out.textContent = JSON.stringify(await api(8006, "/risk/metrics", "POST", {project_id:Number(risk_project_id.value), metric_name:risk_name.value, metric_value:Number(risk_value.value), threshold:Number(risk_threshold.value)}), null, 2); }
    async function riskDashboard(){ risk_out.textContent = JSON.stringify(await api(8006, `/risk/dashboard?project_id=${risk_project_id.value}`, "GET"), null, 2); }
    async function assignRole(){ sec_out.textContent = JSON.stringify(await api(8007, "/rbac/assign", "POST", {username:sec_user.value, role:sec_role.value, permission_group:sec_group.value}), null, 2); }
    async function runSensitive(){ sec_out.textContent = JSON.stringify(await api(8007, "/security/sensitive", "POST", {username:sec_user.value, operation:"delete_record", biometric_verified:true, otp_verified:true}), null, 2); }
    async function listUsers(){ sec_out.textContent = JSON.stringify(await api(8007, "/rbac/users", "GET"), null, 2); }
    async function getAudit(){ audit_out.textContent = JSON.stringify(await api(8003, "/audit", "GET"), null, 2); }
  </script>
</body>
</html>
"""
=======
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="CTMS Frontend")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>CTMS 全功能控制台</title>
  <style>
    body{font-family:Arial;margin:0;background:#f5f7fb}
    header{background:#1e40af;color:#fff;padding:12px 18px}
    .container{padding:16px}
    .card{background:#fff;border-radius:8px;padding:12px;margin-bottom:14px}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    input,select,textarea,button{width:100%;padding:8px;margin-top:6px;box-sizing:border-box}
    button{background:#2563eb;color:#fff;border:0;border-radius:6px;cursor:pointer}
    pre{background:#111827;color:#e5e7eb;padding:10px;border-radius:8px;overflow:auto}
  </style>
</head>
<body>
  <header>CTMS 全功能控制台 | <a href="http://127.0.0.1:8001/docs" style="color:#bfdbfe">Project</a> | <a href="http://127.0.0.1:8002/docs" style="color:#bfdbfe">Randomization</a> | <a href="http://127.0.0.1:8003/docs" style="color:#bfdbfe">Audit</a> | <a href="http://127.0.0.1:8004/docs" style="color:#bfdbfe">Patient</a> | <a href="http://127.0.0.1:8005/docs" style="color:#bfdbfe">Validation</a> | <a href="http://127.0.0.1:8006/docs" style="color:#bfdbfe">Monitoring</a> | <a href="http://127.0.0.1:8007/docs" style="color:#bfdbfe">Security</a></header>
  <div class="container">
    <div class="grid">
      <div class="card">
        <h3>项目与随机化开关</h3>
        <input id="proj_name" placeholder="项目名称" value="肺癌III期"/>
        <select id="proj_rand"><option value="true">开启随机化</option><option value="false">关闭随机化</option></select>
        <button onclick="createProject()">创建项目</button>
        <input id="switch_project_id" placeholder="项目ID"/>
        <select id="switch_enabled"><option value="true">切换为开启</option><option value="false">切换为关闭</option></select>
        <button onclick="toggleSwitch()">切换开关</button>
      </div>
      <div class="card">
        <h3>中心与预算</h3>
        <input id="site_project_id" placeholder="项目ID"/>
        <input id="site_name" placeholder="中心名称" value="北京协和医院"/>
        <input id="site_budget" placeholder="预算" value="500000"/>
        <button onclick="createSite()">创建中心</button>
        <button onclick="listSites()">查询中心</button>
        <pre id="site_out"></pre>
      </div>
    </div>
    <div class="grid">
      <div class="card">
        <h3>患者入组与eICF</h3>
        <input id="pat_project_id" placeholder="项目ID"/>
        <input id="pat_name" placeholder="姓名" value="张三"/>
        <input id="pat_age" placeholder="年龄" value="45"/>
        <select id="pat_severity"><option value="low">low</option><option value="medium">medium</option><option value="high">high</option></select>
        <button onclick="enrollPatient()">入组并分组</button>
        <input id="eicf_patient_id" placeholder="患者ID"/>
        <button onclick="signEicf()">签署eICF</button>
        <button onclick="listPatients()">查询患者</button>
      </div>
      <div class="card">
        <h3>数据校验与清洗</h3>
        <textarea id="clean_payload" rows="6">[{"id":1,"value":120},{"id":2,"value":null},{"id":3,"value":1400}]</textarea>
        <button onclick="cleanData()">执行清洗</button>
        <pre id="clean_out"></pre>
      </div>
    </div>
    <div class="grid">
      <div class="card">
        <h3>风险监控</h3>
        <input id="risk_project_id" placeholder="项目ID"/>
        <input id="risk_name" placeholder="指标名" value="enrollment_delay"/>
        <input id="risk_value" placeholder="指标值" value="45"/>
        <input id="risk_threshold" placeholder="阈值" value="30"/>
        <button onclick="addRisk()">提交风险指标</button>
        <button onclick="riskDashboard()">查看风险仪表盘</button>
        <pre id="risk_out"></pre>
      </div>
      <div class="card">
        <h3>权限安全</h3>
        <input id="sec_user" placeholder="用户名" value="cra_user"/>
        <input id="sec_role" placeholder="角色" value="CRA"/>
        <input id="sec_group" placeholder="权限组" value="monitoring"/>
        <button onclick="assignRole()">分配角色</button>
        <button onclick="runSensitive()">执行敏感操作(双因子)</button>
        <button onclick="listUsers()">查询用户</button>
        <pre id="sec_out"></pre>
      </div>
    </div>
    <div class="card">
      <h3>审计日志</h3>
      <button onclick="getAudit()">刷新审计日志</button>
      <pre id="audit_out"></pre>
    </div>
  </div>
  <script>
    async function api(port, path, method, payload){
      const res = await fetch(`http://127.0.0.1:${port}${path}`, {method, headers: {"Content-Type":"application/json"}, body: payload?JSON.stringify(payload):undefined});
      const data = await res.json();
      if(!res.ok){ alert(JSON.stringify(data)); throw new Error(data.detail || "error"); }
      return data;
    }
    async function createProject(){
      const r = await api(8001, "/projects", "POST", {name: proj_name.value, randomization_enabled: proj_rand.value==="true", protocol_reason: "Intervention"});
      switch_project_id.value = r.project_id; site_project_id.value = r.project_id; pat_project_id.value = r.project_id; risk_project_id.value = r.project_id;
      alert("project_id=" + r.project_id);
    }
    async function toggleSwitch(){ await api(8001, `/projects/${switch_project_id.value}/randomization-switch`, "PUT", {enabled: switch_enabled.value==="true", operator_id: "PM-001", operator_ip: "127.0.0.1", signature: "SIG-PM001", mfa_verified: true}); }
    async function createSite(){ site_out.textContent = JSON.stringify(await api(8001, "/sites", "POST", {project_id:Number(site_project_id.value), site_name:site_name.value, planned_budget:Number(site_budget.value)}), null, 2); }
    async function listSites(){ site_out.textContent = JSON.stringify(await api(8001, `/sites?project_id=${site_project_id.value}`, "GET"), null, 2); }
    async function enrollPatient(){ const r = await api(8004, "/patients", "POST", {project_id:Number(pat_project_id.value), name:pat_name.value, age:Number(pat_age.value), severity:pat_severity.value, operator_id:"INV-001", operator_ip:"127.0.0.1", signature:"SIG-INV001", mfa_verified:true}); eicf_patient_id.value = r.patient_id; alert(JSON.stringify(r)); }
    async function signEicf(){ await api(8004, "/patients/eicf-sign", "POST", {patient_id:Number(eicf_patient_id.value), operator_id:"INV-001", operator_ip:"127.0.0.1", signature:"SIG-INV001", mfa_verified:true}); }
    async function listPatients(){ audit_out.textContent = JSON.stringify(await api(8004, `/patients?project_id=${pat_project_id.value}`, "GET"), null, 2); }
    async function cleanData(){ clean_out.textContent = JSON.stringify(await api(8005, "/clean", "POST", {points: JSON.parse(clean_payload.value)}), null, 2); }
    async function addRisk(){ risk_out.textContent = JSON.stringify(await api(8006, "/risk/metrics", "POST", {project_id:Number(risk_project_id.value), metric_name:risk_name.value, metric_value:Number(risk_value.value), threshold:Number(risk_threshold.value)}), null, 2); }
    async function riskDashboard(){ risk_out.textContent = JSON.stringify(await api(8006, `/risk/dashboard?project_id=${risk_project_id.value}`, "GET"), null, 2); }
    async function assignRole(){ sec_out.textContent = JSON.stringify(await api(8007, "/rbac/assign", "POST", {username:sec_user.value, role:sec_role.value, permission_group:sec_group.value}), null, 2); }
    async function runSensitive(){ sec_out.textContent = JSON.stringify(await api(8007, "/security/sensitive", "POST", {username:sec_user.value, operation:"delete_record", biometric_verified:true, otp_verified:true}), null, 2); }
    async function listUsers(){ sec_out.textContent = JSON.stringify(await api(8007, "/rbac/users", "GET"), null, 2); }
    async function getAudit(){ audit_out.textContent = JSON.stringify(await api(8003, "/audit", "GET"), null, 2); }
  </script>
</body>
</html>
"""
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
