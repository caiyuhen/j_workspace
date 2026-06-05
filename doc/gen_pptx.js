const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "患者数字孪生平台技术架构";

// ===== 颜色主题 =====
const C = {
  bgDark:   "0D1B2A",   // 深蓝黑 - 标题/结尾背景
  bgLight:  "F0F4F8",   // 浅灰蓝 - 内容页背景
  primary:  "1A73E8",   // 主蓝
  gather:   "1565C0",   // 采集层 - 深蓝
  gatherBg: "DBEAFE",   // 采集层卡片背景
  clean:    "0F9D58",   // 清洗层 - 绿
  cleanBg:  "D1FAE5",
  db:       "F4511E",   // 专病库 - 橙红
  dbBg:     "FEE2C5",
  sci:      "9C27B0",   // 科研 - 紫
  sciBg:    "EDE7F6",
  ai:       "1565C0",   // 大模型 - 蓝
  aiBg:     "DBEAFE",
  twin:     "00838F",   // 数字孪生 - 青
  twinBg:   "E0F7FA",
  white:    "FFFFFF",
  dark:     "1A1A2E",
  gray:     "64748B",
  lightGray:"E2E8F0",
  accent:   "FBBC04",   // 金色强调
};

// ===== 辅助函数 =====
function makeShadow() {
  return { type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 };
}

// ===== SLIDE 1: 封面 =====
{
  const s = pres.addSlide();
  s.background = { color: C.bgDark };

  // 顶部装饰条
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: C.accent }, line: { color: C.accent }
  });

  // 左侧竖色块
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.5, h: 5.625,
    fill: { color: C.primary }, line: { color: C.primary }
  });

  // 主标题
  s.addText("患者数字孪生平台", {
    x: 1.0, y: 1.3, w: 8.5, h: 1.1,
    fontSize: 44, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", margin: 0,
  });

  // 副标题
  s.addText("从数据采集到虚拟病患的全链路技术架构", {
    x: 1.0, y: 2.5, w: 8.5, h: 0.6,
    fontSize: 20, fontFace: "Microsoft YaHei",
    color: "B0C4DE", align: "left", margin: 0,
  });

  // 分隔线
  s.addShape(pres.shapes.RECTANGLE, {
    x: 1.0, y: 3.25, w: 3.0, h: 0.04,
    fill: { color: C.accent }, line: { color: C.accent }
  });

  // 四个核心数字
  const stats = [
    { val: "4", lbl: "数据来源" },
    { val: "3", lbl: "应用场景" },
    { val: "N", lbl: "疾病专病库" },
    { val: "1", lbl: "虚拟患者" },
  ];
  stats.forEach((st, i) => {
    const x = 1.0 + i * 2.1;
    s.addText(st.val, {
      x, y: 3.55, w: 1.8, h: 0.7,
      fontSize: 40, fontFace: "Arial Black", bold: true,
      color: C.accent, align: "left", margin: 0,
    });
    s.addText(st.lbl, {
      x, y: 4.25, w: 1.8, h: 0.35,
      fontSize: 12, fontFace: "Microsoft YaHei",
      color: "90A4C4", align: "left", margin: 0,
    });
  });

  // 底部标签
  s.addText("Medical Digital Twin Platform  ·  2026", {
    x: 1.0, y: 5.1, w: 8.5, h: 0.35,
    fontSize: 11, fontFace: "Arial", italic: true,
    color: "506080", align: "left", margin: 0,
  });
}

// ===== SLIDE 2: 总览流程图（核心幻灯片）=====
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };

  // 顶部色带
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.72,
    fill: { color: C.bgDark }, line: { color: C.bgDark }
  });
  s.addText("总览：患者数字孪生全流程架构", {
    x: 0.4, y: 0.1, w: 9.2, h: 0.52,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", margin: 0,
  });

  // ---- 四个主流程框 ----
  // 框配置
  const steps = [
    {
      x: 0.15, title: "① 数据采集", color: C.gather, bg: C.gatherBg,
      lines: ["院内：EHR / EMR", "医学影像（PACS）", "检验 / 检查结果", "院外：可穿戴设备", "电子健康档案"],
    },
    {
      x: 2.55, title: "② 数据清洗", color: C.clean, bg: C.cleanBg,
      lines: ["缺失值 / 异常值处理", "数据标准化（HL7）", "隐私脱敏（HIPAA）", "数据质量评分", "生成结构化数据"],
    },
    {
      x: 4.95, title: "③ 疾病专病库", color: C.db, bg: C.dbBg,
      lines: ["糖尿病专病库", "心血管疾病专病库", "肿瘤专病库", "……（按病种细分）", "高置信度 · 可追溯"],
    },
    {
      x: 7.35, title: "④ 多场景应用", color: C.twin, bg: "E8F4F8",
      lines: ["数据科研平台", "大模型智能应用", "数字孪生平台", "（详见下一页）", ""],
    },
  ];

  steps.forEach((st, i) => {
    // 卡片背景
    s.addShape(pres.shapes.RECTANGLE, {
      x: st.x, y: 0.88, w: 2.22, h: 3.9,
      fill: { color: st.bg }, line: { color: st.color, pt: 1.5 },
      shadow: makeShadow(),
    });
    // 标题色带
    s.addShape(pres.shapes.RECTANGLE, {
      x: st.x, y: 0.88, w: 2.22, h: 0.52,
      fill: { color: st.color }, line: { color: st.color }
    });
    // 标题文字
    s.addText(st.title, {
      x: st.x, y: 0.88, w: 2.22, h: 0.52,
      fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    // 内容列表
    st.lines.forEach((line, j) => {
      if (!line) return;
      s.addShape(pres.shapes.OVAL, {
        x: st.x + 0.12, y: 1.57 + j * 0.56, w: 0.12, h: 0.12,
        fill: { color: st.color }, line: { color: st.color }
      });
      s.addText(line, {
        x: st.x + 0.3, y: 1.52 + j * 0.56, w: 1.85, h: 0.42,
        fontSize: 11, fontFace: "Microsoft YaHei",
        color: C.dark, align: "left", valign: "middle", margin: 0,
      });
    });

    // 箭头（最后一个不需要）
    if (i < 3) {
      s.addShape(pres.shapes.LINE, {
        x: st.x + 2.22, y: 2.83, w: 0.33, h: 0,
        line: { color: C.primary, width: 2 }
      });
      // 箭头三角形
      s.addShape(pres.shapes.RECTANGLE, {
        x: st.x + 2.47, y: 2.74, w: 0.08, h: 0.18,
        fill: { color: C.primary }, line: { color: C.primary }
      });
    }
  });

  // 底部说明栏
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.15, y: 4.92, w: 9.7, h: 0.55,
    fill: { color: "E8EDF4" }, line: { color: C.lightGray, pt: 1 }
  });
  s.addText("核心价值：专病库作为唯一可信数据中台，驱动科研、AI推理与数字孪生三大应用场景，实现[数据 -> 洞察 -> 决策]闭环", {
    x: 0.25, y: 4.96, w: 9.5, h: 0.45,
    fontSize: 11, fontFace: "Microsoft YaHei", italic: true,
    color: C.gray, align: "left", valign: "middle", margin: 0,
  });
}

// ===== SLIDE 3: 三大应用场景 =====
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };

  // 顶部色带
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.72,
    fill: { color: C.bgDark }, line: { color: C.bgDark }
  });
  s.addText("Step 4 · 三大核心应用场景", {
    x: 0.4, y: 0.1, w: 9.2, h: 0.52,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", margin: 0,
  });

  // 专病库入口标签
  s.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 0.88, w: 3.0, h: 0.55,
    fill: { color: C.db }, line: { color: C.db }, shadow: makeShadow(),
  });
  s.addText("疾病专病库（数据中台）", {
    x: 3.5, y: 0.88, w: 3.0, h: 0.55,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });

  // 向下箭头
  s.addShape(pres.shapes.LINE, {
    x: 5.0, y: 1.43, w: 0, h: 0.35,
    line: { color: C.gray, width: 1.5 }
  });

  // 三大分支
  const apps = [
    {
      x: 0.2, color: C.sci, bg: C.sciBg, title: "4.1 数据科研平台",
      items: [
        "支持临床研究全流程",
        "数据探索与统计分析",
        "自动生成科研报告",
        "多中心联合研究支持",
        "数据安全共享（联邦学习）",
      ],
      badge: "科研驱动",
    },
    {
      x: 3.6, color: C.ai, bg: C.aiBg, title: "4.2 大模型智能应用",
      items: [
        "辅助诊疗决策支持",
        "医院运营分析优化",
        "医疗/保险风险预测",
        "医学知识库检索",
        "个性化患者沟通",
      ],
      badge: "AI赋能",
    },
    {
      x: 6.9, color: C.twin, bg: C.twinBg, title: "4.3 数字孪生平台",
      items: [
        "为患者生成虚拟病患",
        "疾病进展动态预测",
        "多治疗方案预演比对",
        "疾病风险早期预警",
        "个性化干预方案生成",
      ],
      badge: "预测驱动",
    },
  ];

  apps.forEach(app => {
    // 卡片
    s.addShape(pres.shapes.RECTANGLE, {
      x: app.x, y: 1.78, w: 3.1, h: 3.6,
      fill: { color: app.bg }, line: { color: app.color, pt: 1.5 },
      shadow: makeShadow(),
    });
    // 标题头
    s.addShape(pres.shapes.RECTANGLE, {
      x: app.x, y: 1.78, w: 3.1, h: 0.55,
      fill: { color: app.color }, line: { color: app.color }
    });
    s.addText(app.title, {
      x: app.x, y: 1.78, w: 3.1, h: 0.55,
      fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    // 内容
    app.items.forEach((item, j) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: app.x + 0.12, y: 2.47 + j * 0.56, w: 0.06, h: 0.26,
        fill: { color: app.color }, line: { color: app.color }
      });
      s.addText(item, {
        x: app.x + 0.26, y: 2.44 + j * 0.56, w: 2.76, h: 0.45,
        fontSize: 11.5, fontFace: "Microsoft YaHei",
        color: C.dark, align: "left", valign: "middle", margin: 0,
      });
    });
    // 徽章
    s.addShape(pres.shapes.RECTANGLE, {
      x: app.x + 1.85, y: 5.1, w: 1.1, h: 0.28,
      fill: { color: app.color }, line: { color: app.color },
    });
    s.addText(app.badge, {
      x: app.x + 1.85, y: 5.1, w: 1.1, h: 0.28,
      fontSize: 9.5, fontFace: "Microsoft YaHei", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
  });

  // 连接线（专病库 → 三个应用）
  const lineTargets = [1.75, 5.15, 8.45];
  lineTargets.forEach(tx => {
    s.addShape(pres.shapes.LINE, {
      x: 5.0, y: 1.78, w: tx - 5.0, h: 0,
      line: { color: C.gray, width: 1, dashType: "dash" }
    });
  });
}

// ===== SLIDE 4: 数字孪生详解 =====
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };

  // 顶部色带
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.72,
    fill: { color: C.twin }, line: { color: C.twin }
  });
  s.addText("数字孪生平台 · 核心价值与应用案例", {
    x: 0.4, y: 0.1, w: 9.2, h: 0.52,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", margin: 0,
  });

  // 左侧：价值说明
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.2, y: 0.9, w: 4.5, h: 4.5,
    fill: { color: C.white }, line: { color: C.lightGray, pt: 1 },
    shadow: makeShadow(),
  });
  s.addText("核心价值：一患者一孪生", {
    x: 0.3, y: 0.98, w: 4.3, h: 0.45,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true,
    color: C.twin, align: "left", margin: 0,
  });

  const values = [
    ["疾病进展预测", "基于历史数据动态模拟未来3~12个月病情变化"],
    ["方案预演比对", "在虚拟患者上测试多种治疗方案，选择最优路径"],
    ["风险早期预警", "提前识别并发症、恶化风险，启动干预"],
    ["个性化干预", "根据虚拟患者反馈生成专属健康管理建议"],
  ];
  values.forEach((v, i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: 1.55 + i * 0.82, w: 0.36, h: 0.36,
      fill: { color: C.twin }, line: { color: C.twin }
    });
    s.addText(`0${i + 1}`, {
      x: 0.3, y: 1.55 + i * 0.82, w: 0.36, h: 0.36,
      fontSize: 11, fontFace: "Arial Black",
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(v[0], {
      x: 0.75, y: 1.52 + i * 0.82, w: 3.8, h: 0.28,
      fontSize: 12, fontFace: "Microsoft YaHei", bold: true,
      color: C.dark, align: "left", margin: 0,
    });
    s.addText(v[1], {
      x: 0.75, y: 1.8 + i * 0.82, w: 3.8, h: 0.28,
      fontSize: 10, fontFace: "Microsoft YaHei",
      color: C.gray, align: "left", margin: 0,
    });
  });

  // 右侧：应用案例
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 0.9, w: 4.7, h: 4.5,
    fill: { color: C.white }, line: { color: C.lightGray, pt: 1 },
    shadow: makeShadow(),
  });
  s.addText("典型应用案例", {
    x: 5.2, y: 0.98, w: 4.5, h: 0.45,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true,
    color: C.twin, align: "left", margin: 0,
  });

  const cases = [
    {
      title: "糖尿病患者 · 血糖管理",
      color: C.sci,
      desc: "患者王某（2型糖尿病）→ 生成虚拟病患 → 预测未来3个月血糖波动曲线 → 优化胰岛素给药方案 → HbA1c下降1.2%",
    },
    {
      title: "心血管高危患者 · 风险预警",
      color: C.ai,
      desc: "患者李某（高血压合并高血脂）→ 识别心梗风险 → 提前90天预警 → 启动抗血小板治疗 → 降低住院率40%",
    },
    {
      title: "肿瘤患者 · 方案选择",
      color: C.db,
      desc: "患者张某（早期肺癌）→ 虚拟病患对比靶向治疗 vs. 手术 → 预测5年生存率 → 辅助MDT多学科决策",
    },
  ];
  cases.forEach((c, i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.1, y: 1.6 + i * 1.2, w: 0.08, h: 0.9,
      fill: { color: c.color }, line: { color: c.color }
    });
    s.addText(c.title, {
      x: 5.28, y: 1.6 + i * 1.2, w: 4.4, h: 0.32,
      fontSize: 12, fontFace: "Microsoft YaHei", bold: true,
      color: C.dark, align: "left", margin: 0,
    });
    s.addText(c.desc, {
      x: 5.28, y: 1.92 + i * 1.2, w: 4.4, h: 0.55,
      fontSize: 10, fontFace: "Microsoft YaHei",
      color: C.gray, align: "left", margin: 0,
    });
  });
}

// ===== SLIDE 5: 数据安全与合规 =====
{
  const s = pres.addSlide();
  s.background = { color: C.bgLight };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.72,
    fill: { color: C.bgDark }, line: { color: C.bgDark }
  });
  s.addText("数据安全与治理合规保障体系", {
    x: 0.4, y: 0.1, w: 9.2, h: 0.52,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", margin: 0,
  });

  const pillars = [
    {
      x: 0.2, color: "D32F2F", bg: "FFEBEE",
      title: "隐私保护",
      icon: "🔒",
      items: ["数据采集前脱敏处理", "符合 HIPAA / GDPR 标准", "患者知情同意管理", "访问权限最小化原则"],
    },
    {
      x: 2.55, color: "1565C0", bg: "E3F2FD",
      title: "数据治理",
      icon: "📋",
      items: ["统一数据字典与标准", "HL7 FHIR 互操作规范", "数据血缘追溯", "质量评分与监控"],
    },
    {
      x: 4.9, color: "2E7D32", bg: "E8F5E9",
      title: "传输安全",
      icon: "🔐",
      items: ["端到端 TLS 1.3 加密", "API 接口鉴权（OAuth2）", "审计日志留存", "数据传输监控告警"],
    },
    {
      x: 7.25, color: "6A1B9A", bg: "F3E5F5",
      title: "合规审计",
      icon: "✅",
      items: ["定期合规审计报告", "三级等保认证", "数据使用授权管理", "监管报告自动生成"],
    },
  ];

  pillars.forEach(p => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: p.x, y: 0.9, w: 2.22, h: 4.0,
      fill: { color: p.bg }, line: { color: p.color, pt: 1.5 },
      shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: p.x, y: 0.9, w: 2.22, h: 0.62,
      fill: { color: p.color }, line: { color: p.color }
    });
    s.addText(`${p.icon}  ${p.title}`, {
      x: p.x, y: 0.9, w: 2.22, h: 0.62,
      fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    p.items.forEach((item, j) => {
      s.addShape(pres.shapes.OVAL, {
        x: p.x + 0.14, y: 1.69 + j * 0.66, w: 0.1, h: 0.1,
        fill: { color: p.color }, line: { color: p.color }
      });
      s.addText(item, {
        x: p.x + 0.32, y: 1.63 + j * 0.66, w: 1.82, h: 0.46,
        fontSize: 10.5, fontFace: "Microsoft YaHei",
        color: C.dark, align: "left", valign: "middle", margin: 0,
      });
    });
  });

  // 底部说明
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.2, y: 5.05, w: 9.6, h: 0.42,
    fill: { color: "FFF9C4" }, line: { color: "F9A825", pt: 1 }
  });
  s.addText("⚡  所有患者数据在进入专病库前均完成脱敏处理，仅存储经授权的匿名化研究数据，确保合规可用", {
    x: 0.3, y: 5.09, w: 9.4, h: 0.34,
    fontSize: 10.5, fontFace: "Microsoft YaHei",
    color: "5D4037", align: "left", valign: "middle", margin: 0,
  });
}

// ===== SLIDE 6: 总结 =====
{
  const s = pres.addSlide();
  s.background = { color: C.bgDark };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.545, w: 10, h: 0.08,
    fill: { color: C.accent }, line: { color: C.accent }
  });

  s.addText("总结", {
    x: 0.6, y: 0.7, w: 4.0, h: 0.5,
    fontSize: 14, fontFace: "Microsoft YaHei",
    color: "90A4C4", align: "left", margin: 0,
  });
  s.addText("构建患者数字孪生\n实现精准医疗新范式", {
    x: 0.6, y: 1.2, w: 8.5, h: 1.6,
    fontSize: 32, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", margin: 0,
  });

  const summary = [
    { num: "01", title: "数据采集", desc: "打通院内 + 院外多源数据" },
    { num: "02", title: "数据治理", desc: "标准化、脱敏、质量保障" },
    { num: "03", title: "专病库", desc: "按疾病分类的高质量数据中台" },
    { num: "04", title: "三大应用", desc: "科研 + AI + 数字孪生协同赋能" },
  ];

  summary.forEach((item, i) => {
    const x = 0.5 + i * 2.3;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.0, w: 2.1, h: 1.85,
      fill: { color: "1A2A3A" }, line: { color: "2A4A6A", pt: 1 }
    });
    s.addText(item.num, {
      x, y: 3.1, w: 2.1, h: 0.5,
      fontSize: 22, fontFace: "Arial Black", bold: true,
      color: C.accent, align: "center", margin: 0,
    });
    s.addText(item.title, {
      x, y: 3.65, w: 2.1, h: 0.38,
      fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
      color: C.white, align: "center", margin: 0,
    });
    s.addText(item.desc, {
      x, y: 4.05, w: 2.1, h: 0.6,
      fontSize: 10, fontFace: "Microsoft YaHei",
      color: "90A4C4", align: "center", margin: 0,
    });
  });
}

// ===== 输出 =====
pres.writeFile({ fileName: "d:/doc/患者数字孪生平台技术架构.pptx" })
  .then(() => console.log("Done: 患者数字孪生平台技术架构.pptx"))
  .catch(e => console.error(e));
