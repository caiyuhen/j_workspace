const fs = require('fs');
const { 
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageBreak
} = require('docx');

const PRIMARY_COLOR = "1a5f7a";
const SECONDARY_COLOR = "58859d";
const BORDER_COLOR = "CCCCCC";
const HEADER_BG = "D5E8F0";

const createHeader = (title) => [
  new Paragraph({
    children: [
      new TextRun({
        text: title,
        bold: true,
        size: 48,
        font: "微软雅黑",
        color: PRIMARY_COLOR
      })
    ],
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 400 }
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "13810357924 | caiyuheng81@outlook.com | 北京 | 硕士 | 22 年技术经验",
        size: 24,
        font: "微软雅黑",
        color: SECONDARY_COLOR
      })
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 }
  })
];

const createSectionTitle = (title, icon) => [
  new Paragraph({
    children: [
      new TextRun({ text: icon + " " + title, bold: true, size: 28, font: "微软雅黑", color: PRIMARY_COLOR }),
    ],
    spacing: { before: 280, after: 120 }
  }),
  new Paragraph({
    borders: {
      bottom: { style: BorderStyle.SINGLE, size: 6, color: PRIMARY_COLOR }
    },
    spacing: { after: 120 }
  })
];

const createBulletPoint = (text, indentLevel = 0) => {
  const indent = indentLevel * 720;
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, font: "微软雅黑", size: 22 })],
    spacing: { after: 60 },
    indent: { left: indent, hanging: 360 }
  });
};

const createJobEntry = (company, role, period, responsibilities) => [
  new Paragraph({
    children: [
      new TextRun({ text: company, bold: true, size: 24, font: "微软雅黑", color: PRIMARY_COLOR }),
      new TextRun({ text: " | " + role, bold: true, size: 24, font: "微软雅黑" })
    ],
    spacing: { before: 180, after: 60 }
  }),
  new Paragraph({
    children: [new TextRun({ text: period, italics: true, size: 22, font: "微软雅黑", color: SECONDARY_COLOR })],
    spacing: { after: 120 }
  }),
  ...responsibilities.map((item) => {
    if (item.type === "subheading") {
      return new Paragraph({
        children: [new TextRun({ text: item.text, bold: true, size: 22, font: "微软雅黑", color: SECONDARY_COLOR })],
        spacing: { before: 100, after: 80 }
      });
    } else if (item.type === "highlight") {
      return new Paragraph({
        children: [new TextRun({ text: "★ " + item.text, bold: true, size: 22, font: "微软雅黑", color: PRIMARY_COLOR })],
        spacing: { after: 60 }
      });
    }
    return createBulletPoint(item.text, item.indent || 0);
  })
];

const createTable = (headers, rows, headerBg = HEADER_BG) => {
  const border = { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR };
  const borders = { top: border, bottom: border, left: border, right: border };
  const colWidth = Math.floor(9360 / headers.length);
  
  const headerRow = new TableRow({
    children: headers.map(h => new TableCell({
      borders,
      width: { size: colWidth, type: WidthType.DXA },
      shading: { fill: headerBg, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 22, font: "微软雅黑" })] })]
    }))
  });
  
  const bodyRows = rows.map(row => new TableRow({
    children: row.map(cell => new TableCell({
      borders,
      width: { size: colWidth, type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text: cell, size: 22, font: "微软雅黑" })] })]
    }))
  }));
  
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: headers.map(() => colWidth),
    rows: [headerRow, ...bodyRows],
    margins: { top: 100, bottom: 100, left: 100, right: 100 }
  });
};

const doc = new Document({
  creator: "蔡宇衡",
  title: "蔡宇衡的简历 - 医疗影像技术总监",
  styles: {
    default: {
      document: {
        run: { font: "微软雅黑", size: 24 }
      }
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 36, bold: true, font: "微软雅黑", color: PRIMARY_COLOR },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 0 }
      }
    ]
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        size: { width: 12240, height: 15840 }
      }
    },
    children: [
      ...createHeader("蔡宇衡"),
      
      ...createSectionTitle("核心优势", "🎯"),
      new Paragraph({
        children: [new TextRun({ text: "医疗影像 AI 技术管理 | 15 年医疗影像算法与产品落地经验，精通 3D 视觉、PyTorch、CUDA 加速，主导多模态医学影像大模型研发与端侧部署", size: 22, font: "微软雅黑" })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "0-1 团队搭建与研发统筹 | 从 0 到 1 组建百人级产研团队，擅长 5-8 人核心攻坚团队快速孵化", size: 22, font: "微软雅黑" })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "端侧 AI 工程化落地 | 深耕 C++/Python/CUDA/TensorRT 技术栈，攻克 GB 级 3D 体数据实时处理", size: 22, font: "微软雅黑" })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "医疗器械全生命周期管理 | 主导 II 类医疗器械从原型到 NMPA 认证，打造 20+ 款 AI 医疗产品", size: 22, font: "微软雅黑" })],
        spacing: { after: 200 }
      }),
      
      ...createSectionTitle("工作经历", "💼"),
      
      ...createJobEntry("安顿健康科技有限公司", "高级算法工程师", "2025.07 - 至今", [
        { type: "subheading", text: "智能穿戴设备 AI 算法研发" },
        { text: "主导慢性病预测模型开发，基于 PPG/ECG 多模态数据构建机器学习 pipeline" },
        { text: "负责端侧模型部署优化，完成从云端训练到智能手表实时推理的工程化落地" },
        { text: "建立企业级数据标准化 SOP，搭建 Hadoop+Spark 大数据平台" }
      ]),
      
      ...createJobEntry("圣方 (上海) 医药研发有限公司", "高级数据科学家 / 高级算法工程师", "2021.05 - 2025.04", [
        { type: "subheading", text: "技术战略与大模型研发" },
        { text: "制定 AI 技术中长期规划，主导医学影像大模型架构优化" },
        { text: "打造 10+ 款 AI 医疗产品完成商业化，牵头 3 项行业标准制定" },
        { type: "highlight", text: "医学影像大模型临床泛化能力提升 30%，推理延迟降低 45%" }
      ]),
      
      ...createJobEntry("心医国际", "副总裁 / VP", "2020.09 - 2021.05", [
        { text: "主导跨部门技术团队管理，构建全链路研发体系" },
        { text: "开发基于知识图谱的 CDSS 及 AI 康复系统，推动 3 款核心产品在 100+ 医院落地" }
      ]),
      
      ...createJobEntry("北京首佑医学科技", "大数据人工智能总监", "2018.09 - 2020.09", [
        { type: "subheading", text: "医学影像 AI 核心算法攻关" },
        { text: "主导 MRI 影像分析模型研发，基于 CNN/RNN 构建抑郁症及脑卒中预测系统" },
        { text: "解析 150 万 + 电子病历构建精神疾病知识图谱" },
        { type: "highlight", text: "技术成果应用于椎管内占位诊断，准确率提升至 95%" }
      ]),
      
      ...createSectionTitle("★ 核心匹配经历", "🏆"),
      ...createJobEntry("安华亿能医疗影像科技", "CTO/CIO", "2012.04 - 2018.09", [
        { type: "subheading", text: "🎯 智能影像识别系统开发（3D 视觉 + 医学影像 AI）" },
        { type: "highlight", text: "颈动脉三维超声诊断系统（全球首创）" },
        { text: "自主研发超声影像识别引擎，实现 3D 斑块自动检测准确率 98.2%", indent: 1 },
        { text: "创新空间自适应性 3D 图像重建算法，血管结构建模误差 < 0.3mm", indent: 1 },
        { text: "基于 ITK/VTK 框架开发 GB 级 3D 体数据处理 pipeline", indent: 1 },
        { type: "highlight", text: "多模态医学影像 AI 平台" },
        { text: "开发 CT/MRI/超声跨模态融合技术，解决异构数据时空对齐难题", indent: 1 },
        { text: "搭建 DICOM 3.0 智能分析系统，支持自动化病灶标注", indent: 1 },
        { text: "基于 PyTorch 构建 3D CNN 网络，肺结节检测敏感度 > 94%", indent: 1 },
        { type: "subheading", text: "🔧 端侧 AI 部署与加速（C++/CUDA/TensorRT）" },
        { text: "基于 CUDA 并行计算实现 3D 影像处理实时加速（推理延迟降低 60%）" },
        { text: "使用 TensorRT 完成模型量化部署，嵌入式设备秒级推理" },
        { type: "subheading", text: "👥 0-1 技术团队搭建" },
        { type: "highlight", text: "从 0 组建 8 人核心技术团队，获 5 项发明专利" }
      ]),
      
      ...createSectionTitle("技术能力矩阵", "🛠️"),
      createTable(
        ["类别", "技能"],
        [
          ["深度学习框架", "PyTorch ⭐⭐⭐⭐⭐、TensorFlow、Scikit-learn"],
          ["3D 视觉算法", "3D CNN、PointNet、ITK/VTK ⭐⭐⭐⭐⭐"],
          ["编程语言", "C++ ⭐⭐⭐⭐⭐、Python ⭐⭐⭐⭐⭐、CUDA ⭐⭐⭐⭐"],
          ["推理加速", "TensorRT ⭐⭐⭐⭐、ONNX、模型量化"],
          ["医疗标准", "DICOM 3.0、CDISC、OMOP、HL7"],
          ["医疗器械合规", "NMPA 注册、ISO 13485、GCP"]
        ]
      ),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      ...createSectionTitle("核心项目经验", "🚀"),
      
      new Paragraph({
        children: [new TextRun({ text: "智能驾驶系统 | 感知融合算法负责人", bold: true, size: 24, font: "微软雅黑", color: PRIMARY_COLOR })],
        spacing: { before: 120, after: 60 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "2019.06 - 2023.07", italics: true, size: 22, font: "微软雅黑", color: SECONDARY_COLOR })],
        spacing: { after: 120 }
      }),
      createBulletPoint("主导激光雷达 + 毫米波雷达 +16 路摄像头多传感器融合算法，时空校准误差 < 50μs"),
      createBulletPoint("构建 CNN+LSTM 级联 3D 目标检测模型，雨雾/夜间场景 98.7% 检测准确率"),
      createBulletPoint("基于 FPN 与注意力机制优化，量产模型仅需 15TOPS 算力"),
      new Paragraph({
        children: [new TextRun({ text: "技术专利：3 项发明专利（时空同步/3D 检测/轨迹追踪）", bold: true, size: 22, font: "微软雅黑", color: PRIMARY_COLOR })],
        spacing: { after: 120 }
      }),
      
      new Paragraph({
        children: [new TextRun({ text: "AI Agent 药物警戒系统 | 技术负责人", bold: true, size: 24, font: "微软雅黑", color: PRIMARY_COLOR })],
        spacing: { before: 120, after: 60 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "2024.01 - 2024.11", italics: true, size: 22, font: "微软雅黑", color: SECONDARY_COLOR })],
        spacing: { after: 120 }
      }),
      createBulletPoint("基于 LangChain+RAG 搭建药物 AE/SAE 智能采集系统"),
      createBulletPoint("设计医学稽查 Agent，定制数据稽查规则引擎"),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      ...createSectionTitle("为什么匹配这个岗位？", "✨"),
      createTable(
        ["JD 要求", "我的匹配点"],
        [
          ["统筹成像设备配套软件技术路线", "15 年医疗影像 AI 经验，主导多模态大模型研发"],
          ["搭建产品全链路数据架构", "构建 GB 级 3D 体数据处理 pipeline，DICOM 智能分析"],
          ["攻克影像处理关键技术问题", "3D 斑块检测 98.2% 准确率，建模误差<0.3mm"],
          ["0-1 搭建 5-8 人技术团队", "安华亿能从 0 组建 8 人核心团队，获 5 项专利"],
          ["精通 PyTorch 与 3D 视觉算法", "PyTorch 深度应用，3D CNN/ITK/VTK 实战经验"],
          ["CUDA/TensorRT 部署加速", "端侧推理延迟降低 60%，嵌入式秒级推理"],
          ["显微影像/类器官处理经验", "医学影像+3D 视觉技术栈可直接迁移"]
        ]
      ),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      ...createSectionTitle("教育背景", "🎓"),
      new Paragraph({
        children: [
          new TextRun({ text: "山东大学", bold: true, size: 24, font: "微软雅黑" }),
          new TextRun({ text: " | 硕士 | 数据科学与大数据技术 | 2004.07 - 2007.06", size: 24, font: "微软雅黑" })
        ],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: "北京科技大学", bold: true, size: 24, font: "微软雅黑" }),
          new TextRun({ text: " | 本科 | 计算机应用 | 1998.07 - 2002.07", size: 24, font: "微软雅黑" })
        ],
        spacing: { after: 200 }
      }),
      
      ...createSectionTitle("资格证书", "📜"),
      createBulletPoint("高级人工智能训练师"),
      createBulletPoint("高级健康管理师"),
      createBulletPoint("大学英语四级（读写精通）"),
      
      new Paragraph({
        children: [new TextRun({ text: "简历优化说明：重点突出医疗影像 AI、3D 视觉、端侧部署、团队搭建四大核心能力。", size: 20, font: "微软雅黑", color: "888888", italics: true })],
        spacing: { before: 400 }
      })
    ]
  }]
});

Packer.toBuffer(doc)
  .then(buffer => fs.writeFileSync("D:/workspace/doc/蔡宇衡的简历 - 医疗影像技术总监版.docx", buffer))
  .then(() => console.log("✅ 简历已成功生成并保存为 Word 文档！"))
  .catch(err => console.error("❌ 生成失败:", err));
