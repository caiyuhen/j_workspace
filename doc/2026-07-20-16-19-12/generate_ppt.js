const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
pres.author = "WorkBuddy";
pres.title = "蚂蚁阿福·安康通·爱牵挂 三大服务体系深度对比分析";

// === 颜色方案 (Ocean Gradient + 自定义) ===
const C = {
  navy: "1E2761",      // 深海军蓝 - 标题/深色背景
  blue: "1677FF",      // 蚂蚁阿福蓝
  green: "52C41A",     // 安康通绿
  orange: "FA8C16",    // 爱牵挂橙
  iceBlue: "CADCFC",   // 冰蓝
  cream: "F5F7FA",     // 浅灰背景
  white: "FFFFFF",
  dark: "1A1A2E",
  textSec: "555555",
  textMut: "888888",
  border: "E0E0E0",
  redAccent: "FF6384",
  gold: "FFC107",
  lightBlue: "D6E8FF",
  lightGreen: "E8FFE8",
  lightOrange: "FFE8CC",
};

const FONT_H = "Arial Black";
const FONT_B = "Arial";

// 辅助函数：添加页脚
function addFooter(slide, pageNum) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 7.15, w: 13.3, h: 0.35,
    fill: { color: C.navy }
  });
  slide.addText("蚂蚁阿福 · 安康通 · 爱牵挂 — 三大服务体系深度对比分析", {
    x: 0.3, y: 7.15, w: 8, h: 0.35,
    fontSize: 9, color: C.white, fontFace: FONT_B, valign: "middle"
  });
  slide.addText(`${pageNum}`, {
    x: 12.5, y: 7.15, w: 0.5, h: 0.35,
    fontSize: 9, color: C.white, fontFace: FONT_B, align: "right", valign: "middle"
  });
}

// 辅助函数：添加标题栏
function addTitleBar(slide, title, subtitle) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 0.9,
    fill: { color: C.navy }
  });
  slide.addText(title, {
    x: 0.4, y: 0.1, w: 10, h: 0.5,
    fontSize: 24, bold: true, color: C.white, fontFace: FONT_H, valign: "middle"
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.4, y: 0.55, w: 10, h: 0.3,
      fontSize: 12, color: C.iceBlue, fontFace: FONT_B, valign: "middle"
    });
  }
}

// ========== Slide 1: 封面 ==========
let slide1 = pres.addSlide();
slide1.background = { color: C.navy };
// 装饰图形
slide1.addShape(pres.shapes.OVAL, {
  x: 9.5, y: -1.5, w: 5, h: 5,
  fill: { color: C.blue, transparency: 70 }
});
slide1.addShape(pres.shapes.OVAL, {
  x: -1, y: 4.5, w: 4, h: 4,
  fill: { color: C.green, transparency: 75 }
});
slide1.addShape(pres.shapes.OVAL, {
  x: 8, y: 5, w: 3, h: 3,
  fill: { color: C.orange, transparency: 75 }
});

slide1.addText("蚂蚁阿福 · 安康通 · 爱牵挂", {
  x: 0.8, y: 1.8, w: 11.7, h: 1,
  fontSize: 44, bold: true, color: C.white, fontFace: FONT_H, align: "center"
});
slide1.addText("三大服务体系深度对比分析", {
  x: 0.8, y: 2.8, w: 11.7, h: 0.8,
  fontSize: 32, color: C.iceBlue, fontFace: FONT_H, align: "center"
});
// 分隔线
slide1.addShape(pres.shapes.LINE, {
  x: 4, y: 3.8, w: 5.3, h: 0,
  line: { color: C.white, width: 1 }
});
slide1.addText("AI应用 · 业务模式 · 财务单位经济 · 续费率 · 履约成本 · 定价策略\n服务体系 · SLA指标 · 质检培训风控 · 服务成本 · 经验教训", {
  x: 0.8, y: 4, w: 11.7, h: 1,
  fontSize: 14, color: C.iceBlue, fontFace: FONT_B, align: "center", lineSpacingMultiple: 1.5
});
slide1.addText("2026年7月", {
  x: 0.8, y: 6.2, w: 11.7, h: 0.5,
  fontSize: 14, color: C.white, fontFace: FONT_B, align: "center"
});

// ========== Slide 2: 目录 ==========
let slide2 = pres.addSlide();
slide2.background = { color: C.cream };
addTitleBar(slide2, "目录", "CONTENTS");

const tocItems = [
  { num: "01", title: "公司概览与AI应用", pages: "P3-P4" },
  { num: "02", title: "业务及盈利模式", pages: "P5" },
  { num: "03", title: "财务情况及单位经济", pages: "P6" },
  { num: "04", title: "续费率分析", pages: "P7" },
  { num: "05", title: "履约成本及应收占比", pages: "P8" },
  { num: "06", title: "定价策略对比", pages: "P9" },
  { num: "07", title: "三大服务体系—场景分类", pages: "P10" },
  { num: "08", title: "能力边界对比", pages: "P11" },
  { num: "09", title: "服务流程SOP", pages: "P12" },
  { num: "10", title: "SLA指标对比", pages: "P13-P16" },
  { num: "11", title: "质检·培训·风控体系", pages: "P17" },
  { num: "12", title: "服务成本分析", pages: "P18-P19" },
  { num: "13", title: "踩过的坑与经验教训", pages: "P20" },
  { num: "14", title: "总结与建议", pages: "P21" },
];

tocItems.forEach((item, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.8 + col * 6.2;
  const y = 1.3 + row * 0.78;
  
  slide2.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 0.6, h: 0.6,
    fill: { color: C.navy }
  });
  slide2.addText(item.num, {
    x: x, y: y, w: 0.6, h: 0.6,
    fontSize: 18, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
  });
  slide2.addText(item.title, {
    x: x + 0.8, y: y, w: 4.5, h: 0.35,
    fontSize: 15, bold: true, color: C.dark, fontFace: FONT_B, valign: "middle"
  });
  slide2.addText(item.pages, {
    x: x + 0.8, y: y + 0.32, w: 4.5, h: 0.25,
    fontSize: 11, color: C.textMut, fontFace: FONT_B, valign: "middle"
  });
});
addFooter(slide2, 2);

// ========== Slide 3: 公司概览 ==========
let slide3 = pres.addSlide();
slide3.background = { color: C.cream };
addTitleBar(slide3, "01 | 公司概览", "三家公司核心指标一览");

const companies = [
  { name: "蚂蚁阿福", color: C.blue, bg: C.lightBlue,
    data: [
      ["月活用户(MAU)", "1500万"],
      ["日均健康咨询", "500万次"],
      ["AI医疗大模型", "HealthBench 62.5分"],
      ["医生AI分身", "2000名医生"],
      ["核心优势", "技术·流量·生态"],
    ]
  },
  { name: "安康通", color: C.green, bg: C.lightGreen,
    data: [
      ["服务老人数", "2800万"],
      ["覆盖省市", "25个"],
      ["智慧指挥中心", "100+个"],
      ["日均救助老人", "39位"],
      ["核心优势", "政府资源·服务网络"],
    ]
  },
  { name: "爱牵挂", color: C.orange, bg: C.lightOrange,
    data: [
      ["家庭用户数", "50万+"],
      ["行业客户", "1000+家"],
      ["呼叫中心响应", "10秒"],
      ["救援到场", "15分钟"],
      ["核心优势", "硬件·适老化设计"],
    ]
  }
];

companies.forEach((comp, i) => {
  const x = 0.5 + i * 4.3;
  // 卡片背景
  slide3.addShape(pres.shapes.RECTANGLE, {
    x: x, y: 1.2, w: 4.0, h: 5.5,
    fill: { color: C.white },
    line: { color: C.border, width: 1 },
    shadow: { type: "outer", blur: 6, offset: 2, angle: 135, opacity: 0.1 }
  });
  // 顶部色条
  slide3.addShape(pres.shapes.RECTANGLE, {
    x: x, y: 1.2, w: 4.0, h: 0.7,
    fill: { color: comp.color }
  });
  slide3.addText(comp.name, {
    x: x, y: 1.2, w: 4.0, h: 0.7,
    fontSize: 20, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
  });
  // 数据行
  comp.data.forEach((row, j) => {
    const ry = 2.1 + j * 0.85;
    slide3.addText(row[0], {
      x: x + 0.2, y: ry, w: 1.8, h: 0.35,
      fontSize: 11, color: C.textMut, fontFace: FONT_B, valign: "middle"
    });
    slide3.addText(row[1], {
      x: x + 0.2, y: ry + 0.3, w: 3.6, h: 0.4,
      fontSize: 16, bold: true, color: comp.color, fontFace: FONT_B, valign: "middle"
    });
    if (j < comp.data.length - 1) {
      slide3.addShape(pres.shapes.LINE, {
        x: x + 0.3, y: ry + 0.75, w: 3.4, h: 0,
        line: { color: C.border, width: 0.5, dashType: "dash" }
      });
    }
  });
});
addFooter(slide3, 3);

// ========== Slide 4: AI应用情况对比 ==========
let slide4 = pres.addSlide();
slide4.background = { color: C.cream };
addTitleBar(slide4, "01 | AI应用情况", "AI服务占比·应用场景·工具和服务策略");

const aiData = [
  { company: "蚂蚁阿福", color: C.blue,
    scenario: "健康陪伴·健康问答·AI诊室·名医AI分身",
    tool: "1T医疗数据·千人标注团队·开源模型第一",
    strategy: "免费+增值服务·B端SaaS收费"
  },
  { company: "安康通", color: C.green,
    scenario: "紧急救助·AI智能看护·数字孪生·AI陪伴机器人",
    tool: "智慧平台提升单店净利率至12%",
    strategy: "AI健康监测+人工服务结合"
  },
  { company: "爱牵挂", color: C.orange,
    scenario: "跌倒判断算法·双重定位·AI+雷达系统·24h人工呼叫",
    tool: "硬件+软件+服务一体化方案",
    strategy: "智能穿戴+云平台+运营服务"
  }
];

aiData.forEach((item, i) => {
  const y = 1.2 + i * 1.85;
  // 左侧公司名
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: y, w: 2.2, h: 1.6,
    fill: { color: item.color }
  });
  slide4.addText(item.company, {
    x: 0.4, y: y, w: 2.2, h: 1.6,
    fontSize: 18, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
  });
  // 右侧内容
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: 2.8, y: y, w: 10.1, h: 1.6,
    fill: { color: C.white },
    line: { color: C.border, width: 1 }
  });
  slide4.addText([
    { text: "应用场景：", options: { bold: true, color: C.dark, fontSize: 12 } },
    { text: item.scenario + "\n", options: { color: C.textSec, fontSize: 11 } },
    { text: "AI工具：", options: { bold: true, color: C.dark, fontSize: 12 } },
    { text: item.tool + "\n", options: { color: C.textSec, fontSize: 11 } },
    { text: "服务策略：", options: { bold: true, color: C.dark, fontSize: 12 } },
    { text: item.strategy, options: { color: C.textSec, fontSize: 11 } }
  ], {
    x: 3.0, y: y + 0.1, w: 9.7, h: 1.4,
    fontFace: FONT_B, valign: "middle", lineSpacingMultiple: 1.3
  });
});
addFooter(slide4, 4);

// ========== Slide 5: 业务及盈利模式 (饼图) ==========
let slide5 = pres.addSlide();
slide5.background = { color: C.cream };
addTitleBar(slide5, "02 | 业务及盈利模式", "三家公司收入构成占比对比");

// 三个饼图并排
const pieCharts = [
  { company: "蚂蚁阿福", x: 0.4,
    data: [
      { name: "保险/金融分销", value: 35, color: "FF6384" },
      { name: "体检/药品电商", value: 25, color: "36A2EB" },
      { name: "B端SaaS", value: 20, color: "FFCE56" },
      { name: "订阅服务", value: 20, color: "8362E6" },
    ]
  },
  { company: "安康通", x: 4.8,
    data: [
      { name: "政府项目(B2G)", value: 50, color: "4BC0C0" },
      { name: "私人付费服务", value: 30, color: "9966FF" },
      { name: "长护险", value: 20, color: "FF9F40" },
    ]
  },
  { company: "爱牵挂", x: 9.2,
    data: [
      { name: "硬件销售", value: 40, color: "C7C7C7" },
      { name: "订阅服务", value: 25, color: "5366FF" },
      { name: "B端SaaS", value: 15, color: "FFCE56" },
      { name: "政府项目", value: 20, color: "4BC0C0" },
    ]
  }
];

pieCharts.forEach(pc => {
  slide5.addChart(pres.charts.PIE, [{
    name: pc.company,
    labels: pc.data.map(d => d.name),
    values: pc.data.map(d => d.value)
  }], {
    x: pc.x, y: 1.2, w: 3.8, h: 3.8,
    showTitle: true, title: pc.company, titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
    showPercent: true,
    chartColors: pc.data.map(d => d.color),
    showLegend: true, legendPos: "b", legendFontSize: 9, legendColor: C.textSec,
    dataLabelColor: C.white, dataLabelFontSize: 10
  });
});

// 底部说明
slide5.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.3, w: 12.5, h: 1.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide5.addText("盈利模式核心差异", {
  x: 0.6, y: 5.4, w: 12, h: 0.3,
  fontSize: 13, bold: true, color: C.navy, fontFace: FONT_H
});
slide5.addText([
  { text: "蚂蚁阿福：", options: { bold: true, color: C.blue, fontSize: 11 } },
  { text: "「免费AI问诊引流 + 保险/体检/药品变现」，依托支付宝12亿用户生态，边际成本递减\n", options: { color: C.textSec, fontSize: 11 } },
  { text: "安康通：", options: { bold: true, color: C.green, fontSize: 11 } },
  { text: "「B2G政府采购 + B2C服务套餐」，2025年营收22.83亿（+7.25%），毛利率19.13%\n", options: { color: C.textSec, fontSize: 11 } },
  { text: "爱牵挂：", options: { bold: true, color: C.orange, fontSize: 11 } },
  { text: "「硬件一次性销售 + 订阅服务年费」，365元/年基础套餐，硬件低毛利引流+服务高毛利盈利", options: { color: C.textSec, fontSize: 11 } }
], {
  x: 0.6, y: 5.7, w: 12, h: 1.0,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.3
});
addFooter(slide5, 5);

// ========== Slide 6: 财务情况及单位经济 (柱状图) ==========
let slide6 = pres.addSlide();
slide6.background = { color: C.cream };
addTitleBar(slide6, "03 | 财务情况及单位经济", "毛利率·ROI·单次服务成本对比");

// 图表：毛利率对比
slide6.addChart(pres.charts.BAR, [
  { name: "毛利率(%)", labels: ["蚂蚁阿福", "安康通", "爱牵挂(硬件)", "爱牵挂(服务)"], values: [50, 19.13, 30, 65] },
  { name: "目标值", labels: ["蚂蚁阿福", "安康通", "爱牵挂(硬件)", "爱牵挂(服务)"], values: [40, 20, 25, 60] }
], {
  x: 0.4, y: 1.2, w: 6, h: 4,
  barDir: "col",
  showTitle: true, title: "毛利率对比 (%)", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, "FF6384"],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 10,
  showLegend: true, legendPos: "b", legendFontSize: 10,
  valAxisMinVal: 0, valAxisMaxVal: 80,
});

// 图表：ROI对比
slide6.addChart(pres.charts.BAR, [{
  name: "ROI",
  labels: ["蚂蚁阿福", "安康通", "爱牵挂", "行业平均"],
  values: [2.5, 1.8, 1.6, 1.2]
}], {
  x: 6.8, y: 1.2, w: 6.1, h: 4,
  barDir: "col",
  showTitle: true, title: "ROI对比 (收入/成本)", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.green],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 12,
  showLegend: false,
  valAxisMinVal: 0, valAxisMaxVal: 3,
});

// 底部说明
slide6.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.4, w: 12.5, h: 1.4,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide6.addText("数据说明", {
  x: 0.6, y: 5.5, w: 12, h: 0.3,
  fontSize: 13, bold: true, color: C.navy, fontFace: FONT_H
});
slide6.addText([
  { text: "• 蚂蚁阿福：研发投入350.3亿元（2025年），医疗大模型成本高但边际成本极低，AI自动回复单次成本仅30元\n", options: { color: C.textSec, fontSize: 11 } },
  { text: "• 安康通：2025年健康养老板块营收22.83亿（+7.25%），毛利率19.13%（-0.55pct），居家护理收入+123%\n", options: { color: C.textSec, fontSize: 11 } },
  { text: "• 爱牵挂：硬件毛利率25-35%，订阅服务毛利率60-70%（规模效应后），单户年ARPU约500元", options: { color: C.textSec, fontSize: 11 } }
], {
  x: 0.6, y: 5.8, w: 12, h: 1.0,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.3
});
addFooter(slide6, 6);

// ========== Slide 7: 续费率对比 ==========
let slide7 = pres.addSlide();
slide7.background = { color: C.cream };
addTitleBar(slide7, "04 | 续费率分析", "不同类型用户的续费率/留存率对比");

slide7.addChart(pres.charts.BAR, [
  { name: "蚂蚁阿福", labels: ["政府项目", "长护险用户", "B端机构", "家庭用户首年", "事故后续费"], values: [null, null, 70, 30, null] },
  { name: "安康通", labels: ["政府项目", "长护险用户", "B端机构", "家庭用户首年", "事故后续费"], values: [85, 80, 75, 40, 95] },
  { name: "爱牵挂", labels: ["政府项目", "长护险用户", "B端机构", "家庭用户首年", "事故后续费"], values: [70, null, 80, 65, 100] }
], {
  x: 0.4, y: 1.2, w: 8, h: 4.5,
  barDir: "col",
  showTitle: true, title: "续费率对比 (%)", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green, C.orange],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 10,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 9,
  showLegend: true, legendPos: "b", legendFontSize: 11,
  valAxisMinVal: 0, valAxisMaxVal: 110,
});

// 右侧核心驱动因素
slide7.addShape(pres.shapes.RECTANGLE, {
  x: 8.8, y: 1.2, w: 4.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide7.addText("续费核心驱动因素", {
  x: 9.0, y: 1.3, w: 3.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});

const drivers = [
  { company: "蚂蚁阿福", color: C.blue, items: "健康档案连续性\n保险转化不破坏信任\n下沉市场付费意愿" },
  { company: "安康通", color: C.green, items: "刚需服务高频使用\n「1+N」服务团队\n政府背书保障基本盘" },
  { company: "爱牵挂", color: C.orange, items: "安全刚需（跌倒触发即续费）\n子女远程关怀工具\n硬件绑定切换成本高" },
];
drivers.forEach((d, i) => {
  const y = 1.8 + i * 1.25;
  slide7.addShape(pres.shapes.RECTANGLE, {
    x: 9.0, y: y, w: 0.08, h: 1.1,
    fill: { color: d.color }
  });
  slide7.addText(d.company, {
    x: 9.2, y: y, w: 3.6, h: 0.25,
    fontSize: 11, bold: true, color: d.color, fontFace: FONT_H
  });
  slide7.addText(d.items, {
    x: 9.2, y: y + 0.25, w: 3.6, h: 0.85,
    fontSize: 10, color: C.textSec, fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
  });
});

// 底部说明
slide7.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide7.addText("关键发现：事故触发后续费率显著提升 — 爱牵挂100%、安康通95%。安全服务的「刚需属性」是续费的最强驱动力。蚂蚁阿福首年留存仅30%，工具属性强是主要痛点。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 12, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide7, 7);

// ========== Slide 8: 履约成本及应收占比 ==========
let slide8 = pres.addSlide();
slide8.background = { color: C.cream };
addTitleBar(slide8, "05 | 履约成本及应收占比", "成本结构对比 + 应收账款风险分析");

// 堆叠柱状图：成本结构
slide8.addChart(pres.charts.BAR, [
  { name: "人力成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [30, 60, 40] },
  { name: "系统成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [40, 10, 25] },
  { name: "场地成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [10, 15, 5] },
  { name: "通信成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [10, 10, 15] },
  { name: "其他", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [10, 5, 15] }
], {
  x: 0.4, y: 1.2, w: 6, h: 4.5,
  barDir: "col",
  showTitle: true, title: "成本结构占比 (%)", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: ["FF6384", "36A2EB", "FFCE56", "4BC0C0", "9966FF"],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendFontSize: 10,
  valAxisMinVal: 0, valAxisMaxVal: 100,
  barGapWidthPct: 60,
  stacked: true,
});

// 右侧：应收账款风险表
slide8.addShape(pres.shapes.RECTANGLE, {
  x: 6.8, y: 1.2, w: 6.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide8.addText("应收账款风险分析", {
  x: 7.0, y: 1.3, w: 5.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});

const arTable = [
  [{ text: "公司", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center" } },
   { text: "政府应收", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center" } },
   { text: "企业应收", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center" } },
   { text: "个人应收", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center" } },
   { text: "风险等级", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center" } }],
  [{ text: "蚂蚁阿福", options: { bold: true, color: C.blue } }, "无", "中等", "低", { text: "低", options: { color: C.green, bold: true } }],
  [{ text: "安康通", options: { bold: true, color: C.green } }, { text: "高(180-270天)", options: { color: C.redAccent, bold: true } }, "中等", "低", { text: "中高", options: { color: C.orange, bold: true } }],
  [{ text: "爱牵挂", options: { bold: true, color: C.orange } }, "中等", "低", "低", { text: "中", options: { color: C.gold, bold: true } }],
];
slide8.addTable(arTable, {
  x: 7.0, y: 1.8, w: 5.8,
  fontSize: 11, fontFace: FONT_B,
  border: { pt: 0.5, color: C.border },
  colW: [1.3, 1.6, 1.0, 0.9, 1.0],
  rowH: 0.45,
  valign: "middle",
});

// 风险说明
slide8.addText("风险提示", {
  x: 7.0, y: 3.5, w: 5.8, h: 0.3,
  fontSize: 12, bold: true, color: C.navy, fontFace: FONT_H
});
slide8.addText([
  { text: "• 安康通：政府项目垫资压力大，应收账款周转180-270天，现金流风险最高\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "• 爱牵挂：政府项目占中等比例，预付制降低个人端风险\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "• 蚂蚁阿福：纯线上模式无政府应收，在线支付即时到账，风险最低\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "\n成本大头：", options: { bold: true, color: C.dark, fontSize: 11 } },
  { text: "蚂蚁阿福→系统研发(40%)、安康通→人力(60%)、爱牵挂→人力+系统均衡", options: { color: C.textSec, fontSize: 10 } }
], {
  x: 7.0, y: 3.8, w: 5.8, h: 1.8,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.3
});
addFooter(slide8, 8);

// ========== Slide 9: 定价策略对比 ==========
let slide9 = pres.addSlide();
slide9.background = { color: C.cream };
addTitleBar(slide9, "06 | 定价策略对比", "定价逻辑·价格区间·策略特点");

const priceData = [
  { company: "蚂蚁阿福", color: C.blue,
    logic: "免费 + 抽佣 + 增值",
    details: [
      "基础服务：免费（建立用户习惯）",
      "保险分销：佣金10-30%",
      "体检服务：引流价（与美年分成）",
      "B端SaaS：5-20万/年"
    ]
  },
  { company: "安康通", color: C.green,
    logic: "B2G政府采购 + B2C市场化",
    details: [
      "B2G：50-150元/人/年（政府补贴）",
      "B2C基础包：365-720元/年",
      "增值服务包：2000-8000元/年",
      "高端定制：ARPU 8000元/年"
    ]
  },
  { company: "爱牵挂", color: C.orange,
    logic: "硬件一次性 + 订阅年费",
    details: [
      "硬件：510-798元（智能手表）",
      "基础服务：365元/年（24h人工值守）",
      "B端SaaS：5-10万/年",
      "呼叫中心外包：100-150元/户/年"
    ]
  }
];

priceData.forEach((item, i) => {
  const y = 1.2 + i * 1.85;
  slide9.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: y, w: 2.5, h: 1.6,
    fill: { color: item.color }
  });
  slide9.addText(item.company, {
    x: 0.4, y: y, w: 2.5, h: 0.8,
    fontSize: 16, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
  });
  slide9.addText(item.logic, {
    x: 0.4, y: y + 0.8, w: 2.5, h: 0.8,
    fontSize: 11, color: C.white, fontFace: FONT_B, align: "center", valign: "middle", italic: true
  });
  
  slide9.addShape(pres.shapes.RECTANGLE, {
    x: 3.1, y: y, w: 9.8, h: 1.6,
    fill: { color: C.white },
    line: { color: C.border, width: 1 }
  });
  item.details.forEach((d, j) => {
    const col = j % 2;
    const row = Math.floor(j / 2);
    slide9.addText("● " + d, {
      x: 3.3 + col * 4.7, y: y + 0.15 + row * 0.7, w: 4.5, h: 0.6,
      fontSize: 11, color: C.textSec, fontFace: FONT_B, valign: "middle"
    });
  });
});
addFooter(slide9, 9);

// ========== Slide 10: 三大服务体系 - 场景分类 ==========
let slide10 = pres.addSlide();
slide10.background = { color: C.cream };
addTitleBar(slide10, "07 | 三大服务体系—场景分类", "基础服务 / 安全应急 / 安全服务 场景覆盖对比");

slide10.addChart(pres.charts.BAR, [
  { name: "蚂蚁阿福", labels: ["基础服务", "安全应急", "安全服务"], values: [3, 0, 6] },
  { name: "安康通", labels: ["基础服务", "安全应急", "安全服务"], values: [15, 6, 5] },
  { name: "爱牵挂", labels: ["基础服务", "安全应急", "安全服务"], values: [12, 6, 8] }
], {
  x: 0.4, y: 1.2, w: 7, h: 4.5,
  barDir: "col",
  showTitle: true, title: "场景覆盖数量对比", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green, C.orange],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 12,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 12,
  showLegend: true, legendPos: "b", legendFontSize: 11,
  valAxisMinVal: 0, valAxisMaxVal: 18,
});

// 右侧场景定义
slide10.addShape(pres.shapes.RECTANGLE, {
  x: 7.8, y: 1.2, w: 5.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide10.addText("场景划分标准", {
  x: 8.0, y: 1.3, w: 4.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});

const sceneDefs = [
  { name: "基础服务", color: C.blue,
    def: "日常生活支持 · 非紧急 · 低频次",
    examples: "助餐、家政、健康咨询、情感关怀、生活代办" },
  { name: "安全应急服务", color: C.redAccent,
    def: "紧急风险处置 · 突发性 · 高风险",
    examples: "跌倒救援、疾病急救、走失寻人、环境安全" },
  { name: "安全服务", color: C.gold,
    def: "持续风险监测 · 预防性 · 数据驱动",
    examples: "生命体征监测、行为异常监测、环境监测" },
];
sceneDefs.forEach((s, i) => {
  const y = 1.8 + i * 1.3;
  slide10.addShape(pres.shapes.RECTANGLE, {
    x: 8.0, y: y, w: 0.08, h: 1.15,
    fill: { color: s.color }
  });
  slide10.addText(s.name, {
    x: 8.2, y: y, w: 4.6, h: 0.3,
    fontSize: 12, bold: true, color: s.color, fontFace: FONT_H
  });
  slide10.addText(s.def, {
    x: 8.2, y: y + 0.3, w: 4.6, h: 0.3,
    fontSize: 10, color: C.dark, fontFace: FONT_B
  });
  slide10.addText("典型场景：" + s.examples, {
    x: 8.2, y: y + 0.6, w: 4.6, h: 0.5,
    fontSize: 9, color: C.textSec, fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
  });
});

// 底部说明
slide10.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide10.addText("蚂蚁阿福聚焦线上AI服务（9个场景），安康通覆盖最全（26个场景），爱牵挂侧重硬件联动场景（26个场景）。安康通在基础服务场景数上领先，爱牵挂在安全服务监测场景更多。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 11, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide10, 10);

// ========== Slide 11: 能力边界对比 (雷达图) ==========
let slide11 = pres.addSlide();
slide11.background = { color: C.cream };
addTitleBar(slide11, "08 | 能力边界对比", "三家公司综合能力雷达图（满分10分）");

slide11.addChart(pres.charts.RADAR, [
  { name: "蚂蚁阿福", labels: ["软件能力", "硬件能力", "人工服务", "AI技术", "服务网络", "成本控制"], values: [9, 2, 6, 10, 8, 9] },
  { name: "安康通", labels: ["软件能力", "硬件能力", "人工服务", "AI技术", "服务网络", "成本控制"], values: [8, 7, 9, 6, 10, 5] },
  { name: "爱牵挂", labels: ["软件能力", "硬件能力", "人工服务", "AI技术", "服务网络", "成本控制"], values: [7, 9, 5, 5, 6, 7] }
], {
  x: 0.4, y: 1.2, w: 7, h: 5.2,
  radarStyle: "standard",
  showTitle: true, title: "综合能力对比", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green, C.orange],
  chartArea: { fill: { color: C.white } },
  catAxisLabelColor: C.dark, catAxisLabelFontSize: 11,
  valAxisMinVal: 0, valAxisMaxVal: 10,
  showLegend: true, legendPos: "b", legendFontSize: 11,
});

// 右侧放弃案例
slide11.addShape(pres.shapes.RECTANGLE, {
  x: 7.8, y: 1.2, w: 5.1, h: 5.2,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide11.addText("关键放弃案例", {
  x: 8.0, y: 1.3, w: 4.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});

const giveUpCases = [
  { company: "蚂蚁阿福", color: C.blue,
    cases: "① 自建线下医疗站点(2021-2022) → ROI<15%，改为与5000+医院对接\n② 自建保险销售团队(2020-2021) → 佣金被监管限制<10%，改为平台对接20+险企" },
  { company: "安康通", color: C.green,
    cases: "① 自建护理院(2016-2019) → ROI<8%，回收周期>12年，改为连锁加盟模式\n② 在线医疗诊断系统(2018-2019) → 医疗纠纷风险高，改为仅健康咨询" },
  { company: "爱牵挂", color: C.orange,
    cases: "① 自建呼叫中心(2014-2023) → 初始投入≥50万，月运营5-8万，改为乐龄平安铃共享模式\n② 复杂功能手表(2014-2018) → 老人不会用，功能使用率<10%，改为极简设计(使用率→80%+)" },
];
giveUpCases.forEach((c, i) => {
  const y = 1.8 + i * 1.5;
  slide11.addShape(pres.shapes.RECTANGLE, {
    x: 8.0, y: y, w: 0.08, h: 1.35,
    fill: { color: c.color }
  });
  slide11.addText(c.company, {
    x: 8.2, y: y, w: 4.6, h: 0.3,
    fontSize: 12, bold: true, color: c.color, fontFace: FONT_H
  });
  slide11.addText(c.cases, {
    x: 8.2, y: y + 0.3, w: 4.6, h: 1.05,
    fontSize: 9, color: C.textSec, fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.3
  });
});
addFooter(slide11, 11);

// ========== Slide 12: 服务流程SOP ==========
let slide12 = pres.addSlide();
slide12.background = { color: C.cream };
addTitleBar(slide12, "09 | 服务流程SOP", "5步流程对比：基础服务 · 安全应急 · 安全服务");

const flows = [
  { company: "安康通", flowType: "基础服务流程", color: C.green,
    steps: [
      { num: "1", title: "需求评估", time: "签约前1-2天", resp: "评估专员" },
      { num: "2", title: "服务匹配", time: "评估后1天内", resp: "系统自动" },
      { num: "3", title: "上门服务", time: "按计划执行", resp: "护理员" },
      { num: "4", title: "质量评价", time: "服务后24h内", resp: "评价系统" },
      { num: "5", title: "续单转化", time: "周期结束前7天", resp: "客户经理" },
    ]
  },
  { company: "爱牵挂", flowType: "安全应急流程", color: C.orange,
    steps: [
      { num: "1", title: "风险感知", time: "实时", resp: "系统自动" },
      { num: "2", title: "10秒人工响应", time: "<10秒", resp: "坐席人员" },
      { num: "3", title: "15分钟到场", time: "城区12分钟", resp: "救援人员" },
      { num: "4", title: "事后回访", time: "24h内", resp: "客服专员" },
      { num: "5", title: "数据归档", time: "事件结束后", resp: "数据管理员" },
    ]
  },
  { company: "蚂蚁阿福", flowType: "安全服务流程", color: C.blue,
    steps: [
      { num: "1", title: "数据接入", time: "实时", resp: "技术团队" },
      { num: "2", title: "AI分析", time: "实时", resp: "AI系统" },
      { num: "3", title: "人工干预", time: "按需", resp: "健康顾问" },
      { num: "4", title: "持续跟踪", time: "按需", resp: "健康顾问" },
      { num: "5", title: "报告生成", time: "日/周/月", resp: "报告系统" },
    ]
  }
];

flows.forEach((flow, i) => {
  const y = 1.2 + i * 1.75;
  // 公司标签
  slide12.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: y, w: 1.8, h: 1.5,
    fill: { color: flow.color }
  });
  slide12.addText(flow.company, {
    x: 0.4, y: y, w: 1.8, h: 0.8,
    fontSize: 14, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
  });
  slide12.addText(flow.flowType, {
    x: 0.4, y: y + 0.8, w: 1.8, h: 0.7,
    fontSize: 10, color: C.white, fontFace: FONT_B, align: "center", valign: "middle"
  });
  
  // 步骤
  const stepW = 2.0;
  const gap = 0.15;
  const startX = 2.4;
  flow.steps.forEach((step, j) => {
    const sx = startX + j * (stepW + gap);
    slide12.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: y + 0.1, w: stepW, h: 1.3,
      fill: { color: C.white },
      line: { color: flow.color, width: 1.5 }
    });
    // 步骤编号圆
    slide12.addShape(pres.shapes.OVAL, {
      x: sx + stepW/2 - 0.2, y: y + 0.2, w: 0.4, h: 0.4,
      fill: { color: flow.color }
    });
    slide12.addText(step.num, {
      x: sx + stepW/2 - 0.2, y: y + 0.2, w: 0.4, h: 0.4,
      fontSize: 14, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
    });
    slide12.addText(step.title, {
      x: sx + 0.05, y: y + 0.65, w: stepW - 0.1, h: 0.3,
      fontSize: 11, bold: true, color: C.dark, fontFace: FONT_B, align: "center", valign: "middle"
    });
    slide12.addText(step.time, {
      x: sx + 0.05, y: y + 0.92, w: stepW - 0.1, h: 0.2,
      fontSize: 9, color: C.textMut, fontFace: FONT_B, align: "center", valign: "middle"
    });
    slide12.addText(step.resp, {
      x: sx + 0.05, y: y + 1.1, w: stepW - 0.1, h: 0.2,
      fontSize: 9, color: flow.color, fontFace: FONT_B, align: "center", valign: "middle"
    });
    // 箭头
    if (j < flow.steps.length - 1) {
      slide12.addText("→", {
        x: sx + stepW - 0.05, y: y + 0.5, w: gap + 0.1, h: 0.5,
        fontSize: 16, color: C.textMut, fontFace: FONT_B, align: "center", valign: "middle"
      });
    }
  });
});
addFooter(slide12, 12);

// ========== Slide 13: SLA - 响应时效 ==========
let slide13 = pres.addSlide();
slide13.background = { color: C.cream };
addTitleBar(slide13, "10 | SLA指标对比（一）响应时效", "响应时间 · 到场时间 · 工单处理时长（越低越好）");

slide13.addChart(pres.charts.BAR, [
  { name: "蚂蚁阿福", labels: ["响应时间(秒)", "城区到场(分钟)", "工单处理(小时)"], values: [5, null, 2] },
  { name: "安康通", labels: ["响应时间(秒)", "城区到场(分钟)", "工单处理(小时)"], values: [10, 12, 4] },
  { name: "爱牵挂", labels: ["响应时间(秒)", "城区到场(分钟)", "工单处理(小时)"], values: [10, 12, 3.5] },
  { name: "目标值", labels: ["响应时间(秒)", "城区到场(分钟)", "工单处理(小时)"], values: [10, 15, 4] }
], {
  x: 0.4, y: 1.2, w: 8, h: 4.5,
  barDir: "col",
  showTitle: true, title: "响应时效对比（越低越好）", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green, C.orange, "FF6384"],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 10,
  showLegend: true, legendPos: "b", legendFontSize: 11,
  valAxisMinVal: 0,
});

// 右侧说明
slide13.addShape(pres.shapes.RECTANGLE, {
  x: 8.8, y: 1.2, w: 4.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide13.addText("数据解读", {
  x: 9.0, y: 1.3, w: 3.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});
slide13.addText([
  { text: "响应时间\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福最快(5秒)，AI自动回复优势明显；安康通和爱牵挂均为10秒人工响应\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "到场时间\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "安康通和爱牵挂均为12分钟，优于目标值15分钟；蚂蚁阿福纯线上无到场需求\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "工单处理时长\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福2小时（AI自动处理），安康通4小时（达标），爱牵挂3.5小时", options: { color: C.textSec, fontSize: 10 } }
], {
  x: 9.0, y: 1.7, w: 3.8, h: 3.8,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
});

slide13.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide13.addText("蚂蚁阿福在响应时效上全面领先，AI驱动的自动处理能力是核心优势。线下到场服务方面，安康通和爱牵挂均优于目标值，体现了成熟的服务网络调度能力。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 11, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide13, 13);

// ========== Slide 14: SLA - 服务质量 ==========
let slide14 = pres.addSlide();
slide14.background = { color: C.cream };
addTitleBar(slide14, "10 | SLA指标对比（二）服务质量", "满意度 · NPS · 首次解决率 · 投诉率");

slide14.addChart(pres.charts.BAR, [
  { name: "蚂蚁阿福", labels: ["满意度(分)", "NPS", "首次解决率(%)", "投诉率(%)"], values: [4.8, 60, 90, 0.5] },
  { name: "安康通", labels: ["满意度(分)", "NPS", "首次解决率(%)", "投诉率(%)"], values: [4.7, 55, 85, 1.0] },
  { name: "爱牵挂", labels: ["满意度(分)", "NPS", "首次解决率(%)", "投诉率(%)"], values: [4.6, 50, 82, 1.5] }
], {
  x: 0.4, y: 1.2, w: 8, h: 4.5,
  barDir: "col",
  showTitle: true, title: "服务质量对比", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green, C.orange],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 10,
  showLegend: true, legendPos: "b", legendFontSize: 11,
  valAxisMinVal: 0,
});

slide14.addShape(pres.shapes.RECTANGLE, {
  x: 8.8, y: 1.2, w: 4.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide14.addText("数据解读", {
  x: 9.0, y: 1.3, w: 3.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});
slide14.addText([
  { text: "满意度\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福4.8分最高，AI回答一致性好；安康通4.7分；爱牵挂4.6分\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "NPS净推荐值\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福60最高（技术信任）；安康通55（服务口碑）；爱牵挂50\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "首次解决率\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福90%（AI一站式）；安康通85%；爱牵挂82%\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "投诉率\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福最低(0.5%)；爱牵挂最高(1.5%)，硬件故障是主因", options: { color: C.textSec, fontSize: 10 } }
], {
  x: 9.0, y: 1.7, w: 3.8, h: 3.8,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
});

slide14.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide14.addText("蚂蚁阿福在服务质量上全面领先，AI驱动带来一致性体验。投诉率与硬件故障率正相关，爱牵挂需重点降低设备故障引发的投诉。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 11, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide14, 14);

// ========== Slide 15: SLA - 成本效率 ==========
let slide15 = pres.addSlide();
slide15.background = { color: C.cream };
addTitleBar(slide15, "10 | SLA指标对比（三）成本效率", "单次服务成本 · ROI · 人均服务量");

slide15.addChart(pres.charts.BAR, [
  { name: "蚂蚁阿福", labels: ["单次成本(元)", "ROI", "人均服务量"], values: [30, 2.5, 100] },
  { name: "安康通", labels: ["单次成本(元)", "ROI", "人均服务量"], values: [45, 1.8, 30] },
  { name: "爱牵挂", labels: ["单次成本(元)", "ROI", "人均服务量"], values: [40, 1.6, 50] },
  { name: "行业平均", labels: ["单次成本(元)", "ROI", "人均服务量"], values: [55, 1.2, 25] }
], {
  x: 0.4, y: 1.2, w: 8, h: 4.5,
  barDir: "col",
  showTitle: true, title: "成本效率对比", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green, C.orange, "FF6384"],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 10,
  showLegend: true, legendPos: "b", legendFontSize: 11,
  valAxisMinVal: 0,
});

slide15.addShape(pres.shapes.RECTANGLE, {
  x: 8.8, y: 1.2, w: 4.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide15.addText("数据解读", {
  x: 9.0, y: 1.3, w: 3.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});
slide15.addText([
  { text: "单次服务成本\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福30元最低（AI自动）；爱牵挂40元；安康通45元（人力密集）\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "ROI（收入/成本）\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福2.5最高；安康通1.8；爱牵挂1.6\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "人均服务量\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福1000人/日（AI放大效应）；爱牵挂50人/坐席；安康通30人/护理员\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "结论\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "AI驱动模式在成本效率上具有压倒性优势，人力密集型模式需通过规模化降本", options: { color: C.textSec, fontSize: 10 } }
], {
  x: 9.0, y: 1.7, w: 3.8, h: 3.8,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
});

slide15.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide15.addText("蚂蚁阿福成本效率全面领先（AI边际成本递减）。安康通和爱牵挂可通过AI替代30-50%基础咨询来降低人力成本，规模化是关键杠杆。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 11, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide15, 15);

// ========== Slide 16: SLA - 安全效果 ==========
let slide16 = pres.addSlide();
slide16.background = { color: C.cream };
addTitleBar(slide16, "10 | SLA指标对比（四）安全效果", "事故处置成功率 · 误报率 · 漏报率 · 预警提前量");

slide16.addChart(pres.charts.BAR, [
  { name: "安康通", labels: ["处置成功率(%)", "误报率(%)", "漏报率(%)", "预警提前(分钟)"], values: [96, 3.5, 0.8, 35] },
  { name: "爱牵挂", labels: ["处置成功率(%)", "误报率(%)", "漏报率(%)", "预警提前(分钟)"], values: [95, 3.5, 1.0, 30] },
  { name: "蚂蚁阿福", labels: ["处置成功率(%)", "误报率(%)", "漏报率(%)", "预警提前(分钟)"], values: [null, null, null, 45] },
  { name: "目标值", labels: ["处置成功率(%)", "误报率(%)", "漏报率(%)", "预警提前(分钟)"], values: [95, 5, 1, 30] }
], {
  x: 0.4, y: 1.2, w: 8, h: 4.5,
  barDir: "col",
  showTitle: true, title: "安全效果对比", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.green, C.orange, C.blue, "FF6384"],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 10,
  showLegend: true, legendPos: "b", legendFontSize: 11,
  valAxisMinVal: 0,
});

slide16.addShape(pres.shapes.RECTANGLE, {
  x: 8.8, y: 1.2, w: 4.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide16.addText("数据解读", {
  x: 9.0, y: 1.3, w: 3.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});
slide16.addText([
  { text: "事故处置成功率\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "安康通96%最高；爱牵挂95%；均超目标值\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "误报率\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "安康通和爱牵挂均为3.5%，远优于行业平均10-15%\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "漏报率\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "安康通0.8%最低；爱牵挂1.0%\n\n", options: { color: C.textSec, fontSize: 10 } },
  { text: "预警提前量\n", options: { bold: true, color: C.dark, fontSize: 12 } },
  { text: "蚂蚁阿福45分钟最长（AI趋势分析）；安康通35分钟；爱牵挂30分钟", options: { color: C.textSec, fontSize: 10 } }
], {
  x: 9.0, y: 1.7, w: 3.8, h: 3.8,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
});

slide16.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide16.addText("安康通在安全效果指标上表现最佳，误报率控制优于行业平均水平。蚂蚁阿福在预警提前量上领先，AI趋势分析能力可提前45分钟预警风险。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 11, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide16, 16);

// ========== Slide 17: 质检培训风控 ==========
let slide17 = pres.addSlide();
slide17.background = { color: C.cream };
addTitleBar(slide17, "11 | 质检·培训·风控体系", "三家公司体系对比（满分10分）");

slide17.addChart(pres.charts.RADAR, [
  { name: "蚂蚁阿福", labels: ["AI质检覆盖", "人工质检深度", "培训体系完整度", "持证上岗率", "风控措施", "应急演练"], values: [10, 7, 9, 8, 9, 5] },
  { name: "安康通", labels: ["AI质检覆盖", "人工质检深度", "培训体系完整度", "持证上岗率", "风控措施", "应急演练"], values: [8, 9, 8, 10, 9, 8] },
  { name: "爱牵挂", labels: ["AI质检覆盖", "人工质检深度", "培训体系完整度", "持证上岗率", "风控措施", "应急演练"], values: [8, 6, 7, 7, 7, 8] }
], {
  x: 0.4, y: 1.2, w: 7, h: 5.2,
  radarStyle: "standard",
  showTitle: true, title: "质检培训风控体系对比", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green, C.orange],
  chartArea: { fill: { color: C.white } },
  catAxisLabelColor: C.dark, catAxisLabelFontSize: 11,
  valAxisMinVal: 0, valAxisMaxVal: 10,
  showLegend: true, legendPos: "b", legendFontSize: 11,
});

// 右侧体系详情
slide17.addShape(pres.shapes.RECTANGLE, {
  x: 7.8, y: 1.2, w: 5.1, h: 5.2,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide17.addText("体系详情", {
  x: 8.0, y: 1.3, w: 4.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});

const qaDetails = [
  { company: "蚂蚁阿福", color: C.blue,
    qa: "AI质检4维度(准确/专业/完整/安全) + 医学团队1000人复核",
    train: "三级标注体系：基础300人→医学400人→专业评测300人",
    risk: "数据脱敏·AI边界识别·高风险100%转人工" },
  { company: "安康通", color: C.green,
    qa: "AI质检100% + 人工抽检30% + 现场质检20%",
    train: "岗前7天 + 在岗每周2h + 急救/护理证100%持证",
    risk: "600+站点消防排查·等保2.0·第三方责任险" },
  { company: "爱牵挂", color: C.orange,
    qa: "AI质检6模块 + 人工抽检10% + 质检团队5人",
    train: "7天岗前 + 3天带教 + 每月应急演练",
    risk: "跌倒误报率<5%·数据加密·权限控制" },
];
qaDetails.forEach((d, i) => {
  const y = 1.8 + i * 1.5;
  slide17.addShape(pres.shapes.RECTANGLE, {
    x: 8.0, y: y, w: 0.08, h: 1.35,
    fill: { color: d.color }
  });
  slide17.addText(d.company, {
    x: 8.2, y: y, w: 4.6, h: 0.25,
    fontSize: 12, bold: true, color: d.color, fontFace: FONT_H
  });
  slide17.addText([
    { text: "质检：", options: { bold: true, fontSize: 9, color: C.dark } },
    { text: d.qa + "\n", options: { fontSize: 9, color: C.textSec } },
    { text: "培训：", options: { bold: true, fontSize: 9, color: C.dark } },
    { text: d.train + "\n", options: { fontSize: 9, color: C.textSec } },
    { text: "风控：", options: { bold: true, fontSize: 9, color: C.dark } },
    { text: d.risk, options: { fontSize: 9, color: C.textSec } }
  ], {
    x: 8.2, y: y + 0.25, w: 4.6, h: 1.1,
    fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
  });
});
addFooter(slide17, 17);

// ========== Slide 18: 服务成本结构 ==========
let slide18 = pres.addSlide();
slide18.background = { color: C.cream };
addTitleBar(slide18, "12 | 服务成本分析（一）", "覆盖1万老人区域年度成本结构（堆叠占比）");

slide18.addChart(pres.charts.BAR, [
  { name: "人力成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [30, 60, 40] },
  { name: "系统成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [40, 10, 25] },
  { name: "场地成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [10, 15, 5] },
  { name: "通信成本", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [10, 10, 15] },
  { name: "其他", labels: ["蚂蚁阿福", "安康通", "爱牵挂"], values: [10, 5, 15] }
], {
  x: 0.4, y: 1.2, w: 7, h: 4.5,
  barDir: "col",
  showTitle: true, title: "成本结构占比 (%)", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: ["FF6384", "36A2EB", "FFCE56", "4BC0C0", "9966FF"],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 12,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendFontSize: 10,
  valAxisMinVal: 0, valAxisMaxVal: 100,
  stacked: true,
  barGapWidthPct: 60,
});

// 右侧成本大头
slide18.addShape(pres.shapes.RECTANGLE, {
  x: 7.8, y: 1.2, w: 5.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide18.addText("成本大头分析", {
  x: 8.0, y: 1.3, w: 4.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});

const costHeaders = [
  { company: "蚂蚁阿福", color: C.blue, main: "系统研发(40%)",
    detail: "医疗大模型·千人标注团队·云资源。人力占30%为医学团队。边际成本随用户增长递减。" },
  { company: "安康通", color: C.green, main: "人力成本(60%)",
    detail: "护理人员·呼叫中心·上门服务团队。系统占10%，场地占15%(社区站点)。规模效应临界点5000人。" },
  { company: "爱牵挂", color: C.orange, main: "人力+系统均衡(65%)",
    detail: "呼叫中心占30%，SaaS平台占25%。通信成本占15%为三家中最高。场地仅5%(轻资产运营)。" },
];
costHeaders.forEach((c, i) => {
  const y = 1.8 + i * 1.3;
  slide18.addShape(pres.shapes.RECTANGLE, {
    x: 8.0, y: y, w: 0.08, h: 1.15,
    fill: { color: c.color }
  });
  slide18.addText(c.company + " — " + c.main, {
    x: 8.2, y: y, w: 4.6, h: 0.3,
    fontSize: 12, bold: true, color: c.color, fontFace: FONT_H
  });
  slide18.addText(c.detail, {
    x: 8.2, y: y + 0.3, w: 4.6, h: 0.85,
    fontSize: 9, color: C.textSec, fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.3
  });
});

slide18.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide18.addText("成本优化方向：AI自动处理30-50%基础咨询降低人力成本；社区站点共享降低场地成本；IoT流量包谈判降低通信成本。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 11, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide18, 18);

// ========== Slide 19: 单老人年服务成本 ==========
let slide19 = pres.addSlide();
slide19.background = { color: C.cream };
addTitleBar(slide19, "12 | 服务成本分析（二）", "年度总成本及单老人年服务成本对比");

slide19.addChart(pres.charts.BAR, [
  { name: "年度总成本(万元)", labels: ["蚂蚁阿福", "安康通", "爱牵挂", "行业平均"], values: [208, 106, 75, 100] },
  { name: "单老人年成本(元)", labels: ["蚂蚁阿福", "安康通", "爱牵挂", "行业平均"], values: [208, 106, 75, 100] }
], {
  x: 0.4, y: 1.2, w: 8, h: 4.5,
  barDir: "col",
  showTitle: true, title: "成本对比（覆盖1万老人）", titleColor: C.dark, titleFontSize: 14, titleFontFace: FONT_H,
  chartColors: [C.blue, C.green],
  chartArea: { fill: { color: C.white }, roundedCorners: true },
  catAxisLabelColor: C.textSec, catAxisLabelFontSize: 11,
  valAxisLabelColor: C.textSec, valAxisLabelFontSize: 10,
  valGridLine: { color: C.border, size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.dark, dataLabelFontSize: 11,
  showLegend: true, legendPos: "b", legendFontSize: 11,
  valAxisMinVal: 0,
});

slide19.addShape(pres.shapes.RECTANGLE, {
  x: 8.8, y: 1.2, w: 4.1, h: 4.5,
  fill: { color: C.white },
  line: { color: C.border, width: 1 }
});
slide19.addText("单位成本衡量", {
  x: 9.0, y: 1.3, w: 3.8, h: 0.35,
  fontSize: 14, bold: true, color: C.navy, fontFace: FONT_H
});

const unitCost = [
  { label: "蚂蚁阿福", value: "2080元/人/年", color: C.blue,
    note: "医学团队+研发投入高，但AI规模化后边际成本递减" },
  { label: "安康通", value: "1065元/人/年", color: C.green,
    note: "人力密集型，在行业正常水位(800-1500元)内" },
  { label: "爱牵挂", value: "750元/人/年", color: C.orange,
    note: "轻资产模式，成本最低；规模效应临界点3000人" },
];
unitCost.forEach((u, i) => {
  const y = 1.8 + i * 1.2;
  slide19.addShape(pres.shapes.RECTANGLE, {
    x: 9.0, y: y, w: 0.08, h: 1.05,
    fill: { color: u.color }
  });
  slide19.addText(u.label, {
    x: 9.2, y: y, w: 3.6, h: 0.25,
    fontSize: 11, bold: true, color: u.color, fontFace: FONT_H
  });
  slide19.addText(u.value, {
    x: 9.2, y: y + 0.25, w: 3.6, h: 0.3,
    fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H
  });
  slide19.addText(u.note, {
    x: 9.2, y: y + 0.55, w: 3.6, h: 0.5,
    fontSize: 9, color: C.textSec, fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.2
  });
});

slide19.addShape(pres.shapes.RECTANGLE, {
  x: 0.4, y: 5.9, w: 12.5, h: 0.9,
  fill: { color: C.navy }
});
slide19.addText("行业正常水位800-1500元/人/年。爱牵挂成本最低(750元)，安康通在正常范围内(1065元)，蚂蚁阿福最高(2080元)但AI规模化后有望大幅降低。", {
  x: 0.6, y: 5.95, w: 12.2, h: 0.8,
  fontSize: 11, color: C.white, fontFace: FONT_B, valign: "middle", italic: true
});
addFooter(slide19, 19);

// ========== Slide 20: 踩过的坑 ==========
let slide20 = pres.addSlide();
slide20.background = { color: C.cream };
addTitleBar(slide20, "13 | 踩过的坑与经验教训", "三家公司关键教训及解决方案");

const pitfalls = [
  { company: "蚂蚁阿福", color: C.blue,
    items: [
      { problem: "用户粘性低", cause: "下载-尝鲜-闲置，工具属性强", solution: "强化健康陪伴，绑定智能设备，构建连续性健康档案" },
      { problem: "商业化与信任矛盾", cause: "用户担心AI建议为推广产品", solution: "明确「AI不替代医生」边界，商业化服务透明标注" },
      { problem: "数据合规风险", cause: "健康数据敏感，监管趋严", solution: "等保2.0认证、数据脱敏、第三方安全审计" },
    ]
  },
  { company: "安康通", color: C.green,
    items: [
      { problem: "政府项目垫资压力大", cause: "应收账款周转180-270天", solution: "供应链金融、拓展私人付费降低依赖" },
      { problem: "人力成本持续上升", cause: "护理人员薪资年增10-15%", solution: "AI替代部分低价值工作、培训体系提升人效" },
      { problem: "服务标准化难", cause: "属地化管理，总部管控弱", solution: "4PS国际标准+数字化监管(GPS/录音/评价)" },
    ]
  },
  { company: "爱牵挂", color: C.orange,
    items: [
      { problem: "自建呼叫中心成本高", cause: "初始投入≥50万，月运营5-8万", solution: "推出乐龄平安铃共享模式，开放API承接" },
      { problem: "硬件功能复杂老人不会用", cause: "未真正适老化，忽视学习成本", solution: "极简设计(大按钮SOS/长续航/自动同步)" },
      { problem: "家庭付费意愿低", cause: "老人不愿自费，子女犹豫", solution: "强调事故后续费、子女远程关怀场景、政府补贴" },
    ]
  }
];

pitfalls.forEach((p, i) => {
  const col = i;
  const x = 0.4 + col * 4.3;
  // 公司标题
  slide20.addShape(pres.shapes.RECTANGLE, {
    x: x, y: 1.2, w: 4.0, h: 0.6,
    fill: { color: p.color }
  });
  slide20.addText(p.company, {
    x: x, y: 1.2, w: 4.0, h: 0.6,
    fontSize: 16, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
  });
  
  p.items.forEach((item, j) => {
    const y = 2.0 + j * 1.65;
    slide20.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 4.0, h: 1.5,
      fill: { color: C.white },
      line: { color: C.border, width: 1 }
    });
    slide20.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 0.08, h: 1.5,
      fill: { color: p.color }
    });
    slide20.addText("⚠ " + item.problem, {
      x: x + 0.2, y: y + 0.05, w: 3.7, h: 0.3,
      fontSize: 12, bold: true, color: C.redAccent, fontFace: FONT_H
    });
    slide20.addText([
      { text: "原因：", options: { bold: true, fontSize: 9, color: C.dark } },
      { text: item.cause + "\n", options: { fontSize: 9, color: C.textSec } },
      { text: "对策：", options: { bold: true, fontSize: 9, color: p.color } },
      { text: item.solution, options: { fontSize: 9, color: C.textSec } }
    ], {
      x: x + 0.2, y: y + 0.35, w: 3.7, h: 1.1,
      fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.3
    });
  });
});
addFooter(slide20, 20);

// ========== Slide 21: 总结与建议 ==========
let slide21 = pres.addSlide();
slide21.background = { color: C.navy };

slide21.addText("总结与建议", {
  x: 0.5, y: 0.5, w: 12, h: 0.8,
  fontSize: 36, bold: true, color: C.white, fontFace: FONT_H, align: "center"
});

// 三列对比
const summaries = [
  { company: "蚂蚁阿福", color: C.blue,
    advantage: "技术壁垒·流量生态·AI驱动",
    challenge: "商业化路径·用户粘性",
    suggestion: "适合需要AI能力的养老机构；看好技术壁垒和数据资产" },
  { company: "安康通", color: C.green,
    advantage: "政府资源·服务网络·全场景覆盖",
    challenge: "政府应收账款·人力成本",
    suggestion: "适合政府项目和全场景养老服务；看好现金流稳定" },
  { company: "爱牵挂", color: C.orange,
    advantage: "硬件·适老化设计·呼叫中心",
    challenge: "硬件竞争·家庭付费意愿",
    suggestion: "适合需要硬件+呼叫中心的机构；看好硬件+服务增长" },
];

summaries.forEach((s, i) => {
  const x = 0.5 + i * 4.3;
  slide21.addShape(pres.shapes.RECTANGLE, {
    x: x, y: 1.6, w: 4.0, h: 3.5,
    fill: { color: C.white, transparency: 90 },
    line: { color: s.color, width: 2 }
  });
  slide21.addShape(pres.shapes.RECTANGLE, {
    x: x, y: 1.6, w: 4.0, h: 0.6,
    fill: { color: s.color }
  });
  slide21.addText(s.company, {
    x: x, y: 1.6, w: 4.0, h: 0.6,
    fontSize: 18, bold: true, color: C.white, fontFace: FONT_H, align: "center", valign: "middle"
  });
  slide21.addText("核心优势", {
    x: x + 0.2, y: 2.3, w: 3.6, h: 0.25,
    fontSize: 11, bold: true, color: s.color, fontFace: FONT_H
  });
  slide21.addText(s.advantage, {
    x: x + 0.2, y: 2.55, w: 3.6, h: 0.5,
    fontSize: 10, color: C.white, fontFace: FONT_B
  });
  slide21.addText("主要挑战", {
    x: x + 0.2, y: 3.1, w: 3.6, h: 0.25,
    fontSize: 11, bold: true, color: C.redAccent, fontFace: FONT_H
  });
  slide21.addText(s.challenge, {
    x: x + 0.2, y: 3.35, w: 3.6, h: 0.4,
    fontSize: 10, color: C.white, fontFace: FONT_B
  });
  slide21.addText("合作建议", {
    x: x + 0.2, y: 3.85, w: 3.6, h: 0.25,
    fontSize: 11, bold: true, color: C.gold, fontFace: FONT_H
  });
  slide21.addText(s.suggestion, {
    x: x + 0.2, y: 4.1, w: 3.6, h: 0.9,
    fontSize: 10, color: C.white, fontFace: FONT_B, lineSpacingMultiple: 1.3
  });
});

// 行业洞察
slide21.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 5.4, w: 12.3, h: 1.5,
  fill: { color: C.white, transparency: 85 },
  line: { color: C.white, width: 1 }
});
slide21.addText("三大行业洞察", {
  x: 0.7, y: 5.5, w: 12, h: 0.3,
  fontSize: 14, bold: true, color: C.gold, fontFace: FONT_H
});
slide21.addText([
  { text: "① AI化是必经之路 ", options: { bold: true, color: C.gold, fontSize: 12 } },
  { text: "— 人力成本上升+老人数量增长，AI将替代30-50%基础服务\n", options: { color: C.white, fontSize: 11 } },
  { text: "② 硬件+服务融合 ", options: { bold: true, color: C.gold, fontSize: 12 } },
  { text: "— 单纯硬件利润薄，单纯服务重资产，「智能硬件+订阅服务」成为主流\n", options: { color: C.white, fontSize: 11 } },
  { text: "③ B2G保基本·B2C提利润 ", options: { bold: true, color: C.gold, fontSize: 12 } },
  { text: "— 政府项目兜底，市场化服务盈利，保险+养老融合提升ARPU值", options: { color: C.white, fontSize: 11 } }
], {
  x: 0.7, y: 5.8, w: 12, h: 1.0,
  fontFace: FONT_B, valign: "top", lineSpacingMultiple: 1.4
});

slide21.addText("数据来源：公司公告、行业研报、公开报道 · 部分数据为估算值", {
  x: 0.5, y: 7.0, w: 12.3, h: 0.3,
  fontSize: 9, color: C.iceBlue, fontFace: FONT_B, align: "center", italic: true
});

// ========== 保存 ==========
pres.writeFile({ fileName: "D:\\workspace\\doc\\2026-07-20-16-19-12\\蚂蚁阿福安康通爱牵挂_三大服务体系对比分析.pptx" })
  .then(() => console.log("PPT generated successfully!"))
  .catch(err => console.error("Error:", err));
