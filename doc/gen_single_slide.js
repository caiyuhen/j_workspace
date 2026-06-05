const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5 inches — 更宽，容纳横向流程

// ===== 色彩系统 =====
const C = {
  bg:       "0D1B2A",   // 深蓝黑背景
  gather:   "1565C0",   gatherBg: "1E3A5F",   // 采集 - 蓝
  clean:    "1B7A3E",   cleanBg:  "1A3D2B",   // 清洗 - 绿
  db:       "B85C00",   dbBg:     "3D2200",   // 专病库 - 橙
  sci:      "7B1FA2",   sciBg:    "2D1040",   // 科研 - 紫
  ai:       "0277BD",   aiBg:     "0A2540",   // 大模型 - 蓝
  twin:     "00838F",   twinBg:   "003040",   // 数字孪生 - 青
  white:    "FFFFFF",
  dimText:  "A0B8D0",
  accent:   "FBBC04",
  arrow:    "4A90D9",
  cardLine: "2A4A6A",
};

function mkShadow() {
  return { type: "outer", color: "000000", blur: 10, offset: 3, angle: 135, opacity: 0.3 };
}

const s = pres.addSlide();
s.background = { color: C.bg };

// ============================================================
// 顶部标题栏
// ============================================================
s.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 13.3, h: 0.65,
  fill: { color: "0A1520" }, line: { color: "0A1520" }
});
// 左侧色块点缀
s.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 0.22, h: 0.65,
  fill: { color: C.accent }, line: { color: C.accent }
});
s.addText("患者数据孪生全链路架构", {
  x: 0.35, y: 0, w: 7, h: 0.65,
  fontSize: 22, fontFace: "Microsoft YaHei", bold: true,
  color: C.white, align: "left", valign: "middle", margin: 0,
});
s.addText("数据采集  →  清洗治理  →  疾病专病库  →  科研 / 大模型 / 数字孪生", {
  x: 7.2, y: 0, w: 5.9, h: 0.65,
  fontSize: 11, fontFace: "Microsoft YaHei",
  color: C.dimText, align: "right", valign: "middle", margin: 0,
});

// ============================================================
// 上排：三个流程步骤卡片（采集 → 清洗 → 专病库）
// ============================================================

// --- 1. 数据采集 ---
const gx = 0.22, gy = 0.82, gw = 3.7, gh = 2.7;
s.addShape(pres.shapes.RECTANGLE, {
  x: gx, y: gy, w: gw, h: gh,
  fill: { color: C.gatherBg }, line: { color: C.gather, pt: 1.2 },
  shadow: mkShadow(),
});
s.addShape(pres.shapes.RECTANGLE, {
  x: gx, y: gy, w: gw, h: 0.46,
  fill: { color: C.gather }, line: { color: C.gather }
});
s.addText("1   数据采集", {
  x: gx + 0.12, y: gy, w: gw - 0.14, h: 0.46,
  fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
  color: C.white, align: "left", valign: "middle", margin: 0,
});
// 内容：院内 / 院外 两列
const gatherIn  = ["EHR / EMR", "医学影像（PACS）", "检验检查结果"];
const gatherOut = ["可穿戴设备（心率）", "电子健康档案", "患者自报数据"];
s.addText("院内数据", {
  x: gx + 0.18, y: gy + 0.56, w: 1.6, h: 0.3,
  fontSize: 11, fontFace: "Microsoft YaHei", bold: true,
  color: C.accent, align: "left", margin: 0,
});
s.addText("院外数据", {
  x: gx + 1.98, y: gy + 0.56, w: 1.6, h: 0.3,
  fontSize: 11, fontFace: "Microsoft YaHei", bold: true,
  color: C.accent, align: "left", margin: 0,
});
gatherIn.forEach((t, i) => {
  s.addShape(pres.shapes.OVAL, {
    x: gx + 0.18, y: gy + 0.98 + i * 0.48, w: 0.09, h: 0.09,
    fill: { color: C.gather }, line: { color: C.gather }
  });
  s.addText(t, {
    x: gx + 0.32, y: gy + 0.93 + i * 0.48, w: 1.4, h: 0.38,
    fontSize: 10.5, fontFace: "Microsoft YaHei",
    color: C.dimText, align: "left", valign: "middle", margin: 0,
  });
});
gatherOut.forEach((t, i) => {
  s.addShape(pres.shapes.OVAL, {
    x: gx + 1.98, y: gy + 0.98 + i * 0.48, w: 0.09, h: 0.09,
    fill: { color: "4A90D9" }, line: { color: "4A90D9" }
  });
  s.addText(t, {
    x: gx + 2.12, y: gy + 0.93 + i * 0.48, w: 1.65, h: 0.38,
    fontSize: 10.5, fontFace: "Microsoft YaHei",
    color: C.dimText, align: "left", valign: "middle", margin: 0,
  });
});
// 竖分隔线
s.addShape(pres.shapes.LINE, {
  x: gx + 1.85, y: gy + 0.56, w: 0, h: 2.0,
  line: { color: C.cardLine, width: 1 }
});

// --- 箭头 1→2 ---
s.addShape(pres.shapes.LINE, {
  x: gx + gw, y: gy + gh / 2, w: 0.45, h: 0,
  line: { color: C.arrow, width: 2.5 }
});
s.addShape(pres.shapes.RECTANGLE, {
  x: gx + gw + 0.37, y: gy + gh / 2 - 0.12, w: 0.1, h: 0.24,
  fill: { color: C.arrow }, line: { color: C.arrow }
});

// --- 2. 数据清洗 ---
const cx = gx + gw + 0.55, cy = gy, cw = 3.7, ch = gh;
s.addShape(pres.shapes.RECTANGLE, {
  x: cx, y: cy, w: cw, h: ch,
  fill: { color: C.cleanBg }, line: { color: C.clean, pt: 1.2 },
  shadow: mkShadow(),
});
s.addShape(pres.shapes.RECTANGLE, {
  x: cx, y: cy, w: cw, h: 0.46,
  fill: { color: C.clean }, line: { color: C.clean }
});
s.addText("2   数据清洗与治理", {
  x: cx + 0.12, y: cy, w: cw - 0.14, h: 0.46,
  fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
  color: C.white, align: "left", valign: "middle", margin: 0,
});
const cleanItems = [
  ["缺失值 / 异常值处理", "保留有效数据，提升质量"],
  ["数据标准化（HL7）",   "统一编码与格式规范"],
  ["隐私脱敏（HIPAA）",  "患者数据合规匿名化"],
  ["数据质量评分",       "生成可信度报告"],
];
cleanItems.forEach(([title, sub], i) => {
  s.addShape(pres.shapes.RECTANGLE, {
    x: cx + 0.15, y: cy + 0.6 + i * 0.54, w: 0.06, h: 0.32,
    fill: { color: C.clean }, line: { color: C.clean }
  });
  s.addText(title, {
    x: cx + 0.28, y: cy + 0.58 + i * 0.54, w: 3.3, h: 0.28,
    fontSize: 11.5, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", margin: 0,
  });
  s.addText(sub, {
    x: cx + 0.28, y: cy + 0.85 + i * 0.54, w: 3.3, h: 0.22,
    fontSize: 9.5, fontFace: "Microsoft YaHei",
    color: C.dimText, align: "left", margin: 0,
  });
});

// --- 箭头 2→3 ---
s.addShape(pres.shapes.LINE, {
  x: cx + cw, y: cy + ch / 2, w: 0.45, h: 0,
  line: { color: C.arrow, width: 2.5 }
});
s.addShape(pres.shapes.RECTANGLE, {
  x: cx + cw + 0.37, y: cy + ch / 2 - 0.12, w: 0.1, h: 0.24,
  fill: { color: C.arrow }, line: { color: C.arrow }
});

// --- 3. 疾病专病库（核心枢纽）---
const dx = cx + cw + 0.55, dy = gy, dw = 4.35, dh = gh;
s.addShape(pres.shapes.RECTANGLE, {
  x: dx, y: dy, w: dw, h: dh,
  fill: { color: C.dbBg }, line: { color: C.db, pt: 2 },
  shadow: mkShadow(),
});
s.addShape(pres.shapes.RECTANGLE, {
  x: dx, y: dy, w: dw, h: 0.46,
  fill: { color: C.db }, line: { color: C.db }
});
s.addText("3   疾病专病库（核心数据中台）", {
  x: dx + 0.12, y: dy, w: dw - 0.14, h: 0.46,
  fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
  color: C.white, align: "left", valign: "middle", margin: 0,
});
// 三个病种库 tag
const dbTags = ["糖尿病专病库", "心血管疾病专病库", "肿瘤专病库", "...（按病种扩展）"];
const dbColors = [C.gather, C.clean, C.twin, C.cardLine];
dbTags.forEach((tag, i) => {
  s.addShape(pres.shapes.RECTANGLE, {
    x: dx + 0.2 + (i % 2) * 2.05, y: dy + 0.66 + Math.floor(i / 2) * 0.68, w: 1.85, h: 0.5,
    fill: { color: dbColors[i] }, line: { color: dbColors[i] },
    shadow: mkShadow(),
  });
  s.addText(tag, {
    x: dx + 0.2 + (i % 2) * 2.05, y: dy + 0.66 + Math.floor(i / 2) * 0.68, w: 1.85, h: 0.5,
    fontSize: 10.5, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });
});
// 特征说明
s.addShape(pres.shapes.RECTANGLE, {
  x: dx + 0.2, y: dy + 2.12, w: 3.9, h: 0.36,
  fill: { color: "2A1800" }, line: { color: C.db, pt: 1 }
});
s.addText("多源异构数据  →  疾病标签化  →  结构化存储  →  质量验证", {
  x: dx + 0.22, y: dy + 2.14, w: 3.86, h: 0.32,
  fontSize: 9.5, fontFace: "Microsoft YaHei", italic: true,
  color: C.accent, align: "center", valign: "middle", margin: 0,
});

// ============================================================
// 向下箭头（专病库 → 三大应用）
// ============================================================
const arrowX = dx + dw / 2 - 0.05;
const topRowBottom = gy + gh;
s.addShape(pres.shapes.LINE, {
  x: arrowX, y: topRowBottom, w: 0, h: 0.32,
  line: { color: C.accent, width: 2.5 }
});
s.addShape(pres.shapes.RECTANGLE, {
  x: arrowX - 0.1, y: topRowBottom + 0.24, w: 0.2, h: 0.1,
  fill: { color: C.accent }, line: { color: C.accent }
});
s.addText("多场景应用", {
  x: arrowX + 0.18, y: topRowBottom + 0.05, w: 1.6, h: 0.3,
  fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
  color: C.accent, align: "left", margin: 0,
});

// ============================================================
// 下排：三大应用场景（科研 | 大模型 | 数字孪生）
// ============================================================
const appY = topRowBottom + 0.42;
const appH = 7.5 - appY - 0.22;
const appW = (13.3 - 0.22 * 2 - 0.3 * 2) / 3; // 均分宽度
const apps = [
  {
    title: "4.1   数据科研平台",
    color: C.sci, bg: C.sciBg,
    badge: "科研驱动",
    items: [
      "支持临床研究全流程管理",
      "数据探索与统计分析",
      "自动生成科研报告",
      "多中心联合研究（联邦学习）",
    ],
    note: "数据探索 → 统计分析 → 报告生成",
  },
  {
    title: "4.2   大模型智能应用",
    color: C.ai, bg: C.aiBg,
    badge: "AI 赋能",
    items: [
      "辅助诊疗决策支持",
      "医院运营分析优化",
      "医疗 / 保险风险预测",
      "医学知识库检索问答",
    ],
    note: "医疗决策 → 保险风控 → 知识检索",
  },
  {
    title: "4.3   数字孪生平台",
    color: C.twin, bg: C.twinBg,
    badge: "预测驱动",
    items: [
      "为患者生成虚拟病患模型",
      "疾病进展动态预测",
      "多治疗方案预演比对",
      "个性化干预方案生成",
    ],
    note: "一患者一孪生 → 动态预测 → 精准干预",
  },
];

apps.forEach((app, i) => {
  const ax = 0.22 + i * (appW + 0.3);
  // 卡片
  s.addShape(pres.shapes.RECTANGLE, {
    x: ax, y: appY, w: appW, h: appH,
    fill: { color: app.bg }, line: { color: app.color, pt: 1.5 },
    shadow: mkShadow(),
  });
  // 标题头
  s.addShape(pres.shapes.RECTANGLE, {
    x: ax, y: appY, w: appW, h: 0.46,
    fill: { color: app.color }, line: { color: app.color }
  });
  s.addText(app.title, {
    x: ax + 0.1, y: appY, w: appW - 0.12, h: 0.46,
    fontSize: 12.5, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "left", valign: "middle", margin: 0,
  });
  // 要点列表
  app.items.forEach((item, j) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: ax + 0.16, y: appY + 0.6 + j * 0.56, w: 0.055, h: 0.32,
      fill: { color: app.color }, line: { color: app.color }
    });
    s.addText(item, {
      x: ax + 0.28, y: appY + 0.57 + j * 0.56, w: appW - 0.38, h: 0.44,
      fontSize: 11, fontFace: "Microsoft YaHei",
      color: C.white, align: "left", valign: "middle", margin: 0,
    });
  });
  // 底部注释条
  const noteY = appY + appH - 0.42;
  s.addShape(pres.shapes.RECTANGLE, {
    x: ax, y: noteY, w: appW, h: 0.42,
    fill: { color: "0A0A1A" }, line: { color: app.color, pt: 1 }
  });
  s.addText(app.note, {
    x: ax + 0.1, y: noteY + 0.02, w: appW - 0.2, h: 0.38,
    fontSize: 9.5, fontFace: "Microsoft YaHei", italic: true,
    color: app.color, align: "center", valign: "middle", margin: 0,
  });
  // 徽章
  s.addShape(pres.shapes.RECTANGLE, {
    x: ax + appW - 1.08, y: appY + 0.55, w: 0.96, h: 0.3,
    fill: { color: app.color }, line: { color: app.color }
  });
  s.addText(app.badge, {
    x: ax + appW - 1.08, y: appY + 0.55, w: 0.96, h: 0.3,
    fontSize: 9, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "center", valign: "middle", margin: 0,
  });
});

// ============================================================
// 底部版权栏
// ============================================================
s.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 7.42, w: 13.3, h: 0.08,
  fill: { color: C.accent }, line: { color: C.accent }
});

// ============================================================
// 输出
// ============================================================
pres.writeFile({ fileName: "d:/doc/患者数字孪生单页流程图.pptx" })
  .then(() => console.log("Done!"))
  .catch(e => console.error(e));
