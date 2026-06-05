const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
       Header, Footer, AlignmentType, PageOrientation, BorderStyle, WidthType,
       ShadingType, LevelFormat, PageBreak, HeadingLevel } = require('docx');

// 读取简历内容
const fs = require('fs');
const path = require('path');
const markdownPath = path.join('D:', 'doc', '蔡宇衡的简历-AI 技术总监优化版.md');
const markdownContent = fs.readFileSync(markdownPath, 'utf-8');

// 定义颜色
const COLORS = {
  PRIMARY: '2E75B6',    // 深蓝 - 主标题
  SECONDARY: '1F4E79',  // 深蓝 - 次级标题
  ACCENT: '5B9BD5',     // 蓝 - 强调色
  TEXT: '2E2E2E',       // 深灰 - 正文
  DATE: '666666',       // 灰色 - 日期
  BORDER: 'D3D3D3'      // 浅灰 - 边框
};

// 创建简历文档
const resumeDoc = new Document({
  creator: '蔡宇衡',
  title: 'AI 技术总监简历',
  subject: '个人简历',
  
  // 字体和样式定义
  styles: {
    default: { 
      document: { 
        run: { 
          font: "Microsoft YaHei", 
          size: 24,
          color: COLORS.TEXT
        } 
      } 
    },
    paragraphStyles: [
      {
        id: "TitleStyle",
        name: "Title Style",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: {
          size: 40,
          bold: true,
          color: COLORS.PRIMARY,
          font: "Microsoft YaHei"
        },
        paragraph: {
          spacing: { before: 360, after: 360 },
          alignment: AlignmentType.CENTER
        }
      },
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: {
          size: 28,
          bold: true,
          color: COLORS.PRIMARY,
          font: "Microsoft YaHei"
        },
        paragraph: {
          spacing: { before: 240, after: 180 },
          border: {
            bottom: { style: BorderStyle.SINGLE, size: 6, color: COLORS.PRIMARY, space: 1 }
          }
        }
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: {
          size: 26,
          bold: true,
          color: COLORS.SECONDARY,
          font: "Microsoft YaHei"
        },
        paragraph: {
          spacing: { before: 200, after: 140 }
        }
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: {
          size: 24,
          bold: true,
          color: COLORS.ACCENT,
          font: "Microsoft YaHei"
        },
        paragraph: {
          spacing: { before: 160, after: 120 }
        }
      },
      {
        id: "ContactStyle",
        name: "Contact Style",
        basedOn: "Normal",
        run: {
          size: 24,
          color: COLORS.TEXT,
          font: "Microsoft YaHei"
        },
        paragraph: {
          spacing: { before: 60, after: 240 },
          alignment: AlignmentType.CENTER
        }
      },
      {
        id: "BulletStyle",
        name: "Bullet Style",
        basedOn: "Normal",
        run: {
          size: 22,
          color: COLORS.TEXT,
          font: "Microsoft YaHei"
        },
        paragraph: {
          spacing: { before: 20, after: 20 },
          indent: { left: 720, hanging: 360 }
        }
      },
      {
        id: "DateStyle",
        name: "Date Style",
        run: {
          size: 22,
          color: COLORS.DATE,
          font: "Arial",
          italic: true
        }
      },
      {
        id: "HighlightStyle",
        name: "Highlight Style",
        run: {
          size: 22,
          bold: true,
          color: COLORS.SECONDARY,
          font: "Microsoft YaHei"
        }
      }
    ]
  },

  // 列表定义
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: "•",
          alignment: AlignmentType.LEFT,
          style: {
            paragraph: { indent: { left: 720, hanging: 360 } }
          }
        }]
      },
      {
        reference: "numbers",
        levels: [{
          level: 0,
          format: LevelFormat.DECIMAL,
          text: "%1.",
          alignment: AlignmentType.LEFT,
          style: {
            paragraph: { indent: { left: 720, hanging: 360 } }
          }
        }]
      }
    ]
  },

  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1080, bottom: 1440, left: 1080 }, // 1 英寸上/下，0.75 英寸左/右
        size: { width: 12240, height: 15840 } // US Letter
      }
    },
    
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            text: "蔡宇衡 - AI 技术总监简历",
            style: "DateStyle",
            alignment: AlignmentType.RIGHT,
            spacing: { after: 0 }
          })
        ]
      })
    },
    
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            children: [
              new TextRun({ text: "第 ", style: "DateStyle" }),
              new TextRun({ children: [require('docx').PageNumber.CURRENT], style: "DateStyle" }),
              new TextRun({ text: " 页", style: "DateStyle" })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { before: 0 }
          })
        ]
      })
    },

    children: [
      // ========== 标题部分 ==========
      new Paragraph({ 
        text: "蔡宇衡", 
        style: "TitleStyle",
        spacing: { after: 120 }
      }),

      // ========== 联系方式 ==========
      new Paragraph({ 
        children: [
          new TextRun({ text: "📞 13810357924", style: "ContactStyle" }),
          new TextRun({ text: "  |  ", style: "ContactStyle" }),
          new TextRun({ text: "📧 caiyuheng81@outlook.com", style: "ContactStyle" }),
          new TextRun({ text: "  |  ", style: "ContactStyle" }),
          new TextRun({ text: "📍 北京", style: "ContactStyle" })
        ]
      }),

      new Paragraph({ children: [new PageBreak()] }),

      // ========== 求职意向 ==========
      new Paragraph({ text: "求职意向", style: "Heading1" }),
      
      createTable([
        ["目标职位", "AI 技术总监 / 技术 VP / CTO"],
        ["期望薪资", "60-85k×16 薪"],
        ["工作地点", "北京"],
        ["行业方向", "人工智能、医疗健康、SaaS 平台"]
      ], true),

      // ========== 核心优势 ==========
      new Paragraph({ text: "核心优势", style: "Heading1" }),

      // 技术战略与架构规划
      new Paragraph({ text: "🎯 技术战略与架构规划", style: "Heading3" }),
      createBulletList([
        "22 年软件开发经验，15 年技术管理背景，擅长制定中长期技术演进路线图，主导前端框架升级、微服务架构改造、API 网关解耦、BFF 层建设等系统性技术决策",
        "具备从 0 到 1 组建百人级产研团队经验，建立跨部门研发管理体系，对系统连续性、AI 落地、研发交付节奏负总责",
        "精通微服务架构设计，能在关键技术问题上做兜底决策，管理外包运维伙伴服务质量与 SLA"
      ]),

      // 大模型应用与技术落地
      new Paragraph({ text: "🤖 大模型应用与技术落地", style: "Heading3" }),
      createBulletList([
        "深度实践 LLM 应用开发，精通 Prompt Engineering、RAG 检索增强、Agent 编排、Function Calling、Skill 框架设计，独立交付过 AI Agent 系统上线",
        "熟悉 LangChain、LlamaIndex、Dify、AutoGen 等主流 LLM 应用框架，具备多模态医学影像大模型优化与训练策略设计经验",
        "主导构建企业级 RAG 知识库系统，实现文档分词、向量存储、语义检索的全链路技术闭环"
      ]),

      // 医疗行业与 SaaS 经验
      new Paragraph({ text: "🏥 医疗行业与 SaaS 经验", style: "Heading3" }),
      createBulletList([
        "15 年深耕医疗健康领域，熟悉 ICH GCP、FDA 21 CFR Part 11、CDISC/SDTM 等合规标准",
        "主导开发 CTMS+EDC 临床试验管理系统，具备私有部署 + 多租户 SaaS 系统完整架构经验",
        "熟悉企业微信应用生态，有医疗行业政企 SaaS 产品落地经验"
      ]),

      // 跨组织协作与团队管理
      new Paragraph({ text: "👥 跨组织协作与团队管理", style: "Heading3" }),
      createBulletList([
        "擅长在涉及多个利益相关方（合作技术单位、机构 IT、业务方）的复杂协作场景下，维持稳定合作关系同时守住团队工作节奏与决策边界",
        "牵头 40+ 真实世界研究项目，主导国家级课题申报及行业标准制定（NMPA/CDE/北京大学合作）"
      ]),

      new Paragraph({ children: [new PageBreak()] }),

      // ========== 工作经历 ==========
      new Paragraph({ text: "工作经历", style: "Heading1" }),

      // 安顿健康科技
      createWorkExperience(
        "安顿健康科技有限公司",
        "高级算法工程师（技术负责人）",
        "2025.07 - 至今",
        [
          new Paragraph({ text: "核心职责：", style: "HighlightStyle", spacing: { before: 120 } }),
          new Paragraph({ 
            children: [
              new TextRun({ text: "• ", style: "BulletStyle" }),
              new TextRun({ text: "制定 AI 技术中长期发展规划，主导跨部门技术协作机制建设", style: "BulletStyle" })
            ]
          }),
          new Paragraph({ 
            children: [
              new TextRun({ text: "• ", style: "BulletStyle" }),
              new TextRun({ text: "负责智能穿戴设备健康预测系统架构设计，管理外包开发团队 SLA 交付质量", style: "BulletStyle" })
            ]
          }),
          new Paragraph({ text: "重点项目：", style: "HighlightStyle", spacing: { before: 120 } }),
          new Paragraph({ text: "1. 中医智诊机器人系统（AI Agent 实践）", style: "Heading3", spacing: { before: 80 } }),
          createBulletList([
            "技术架构决策：基于 LangChain + RAG + AutoGen 构建多 Agent 协作框架，设计 Skill 框架扩展机制",
            "RAG 知识库构建：基于《黄帝内经》《伤寒杂病论》等中医典籍建立知识体系（8 万 + 方剂、2000+ 证候、9000+ 中药材）",
            "多模态融合：结合图像识别（望诊）、传感器数据（切诊）、智能问答（问诊）实现四诊法数字化",
            "成果：完成系统从架构设计到上线的全流程，支持临床辅助决策"
          ]),
          new Paragraph({ text: "2. 企业级大数据平台架构", style: "Heading3", spacing: { before: 80 } }),
          createBulletList([
            "技术选型：基于 Hadoop/Spark 构建高并发数据处理平台，设计数据标准化 SOP 与安全 SOP",
            "数据治理：制定元数据管理、数据质量监控、数据生命周期管理方案，开发数据血缘追踪工具",
            "跨团队协作：协调业务部门、数据团队、开发团队需求，确保平台按期交付"
          ])
        ]
      ),

      // 圣方上海
      createWorkExperience(
        "圣方 (上海) 医药研发有限公司",
        "高级数据科学家 / 高级算法工程师（技术负责人）",
        "2021.05 - 2025.04",
        [
          new Paragraph({ text: "核心职责：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "制定 AI 技术演进路线图，主导跨部门研发管理体系建设",
            "负责大模型应用方向技术决策，推动算法创新到产品落地全流程贯通"
          ]),
          new Paragraph({ text: "关键技术成果：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "技术战略：主导 AI 技术中长期规划，建立从算法研发到产品注册交付的完整闭环",
            "大模型平台：优化医学影像大模型架构，推动多模态融合研究，提升模型临床泛化能力",
            "商业化落地：主导 10+ 款 AI 医疗产品从原型设计到 NMPA 注册交付的全周期管理",
            "科研生态：牵头与国内外机构合作研究，参与制定 3 项行业标准",
            "团队建设：搭建高绩效研发团队，建立技术人才选拔培养机制"
          ])
        ]
      ),

      // 心医国际
      createWorkExperience(
        "心医国际",
        "副总裁 / 技术 VP",
        "2020.09 - 2021.05",
        [
          new Paragraph({ text: "核心职责：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "主导跨部门技术团队管理，构建全链路研发体系",
            "统筹技术路线图规划，对系统连续性、交付节奏负总责"
          ]),
          new Paragraph({ text: "关键成果：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "SaaS 平台架构：完成脑科学及肿瘤专科 SaaS 平台架构设计，支持私有部署 + 多租户模式",
            "CDSS 系统：构建基于知识图谱的临床决策支持系统及 AI 康复系统",
            "联邦学习平台：开发数据交易平台，实现隐私保护下的多中心协作",
            "区域医疗协同：陕西/贵州省级项目支持 100+ 医院急救体系协同数据交互",
            "产品落地：推动 3 款核心产品在医疗机构快速落地，药物警戒系统 300+ 医院分布式部署"
          ])
        ]
      ),

      // 北京首佑医学科技
      createWorkExperience(
        "北京首佑医学科技",
        "大数据人工智能总监",
        "2018.09 - 2020.09",
        [
          new Paragraph({ text: "核心职责：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "主导 AI 技术团队建设与技术路线规划",
            "负责医疗知识图谱与 AI 辅助诊断系统架构设计"
          ]),
          new Paragraph({ text: "关键成果：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "知识图谱：通过 NLP 技术解析 150 万 + 电子病历构建精神疾病知识图谱，支撑京津冀三地医疗数据平台建设",
            "核心算法：主导语音识别（CNN/RNN）与 MRI 影像分析模型研发，支撑国自然课题",
            "产品落地：设计双抗药物浓度动态监测算法，完成 6 医院临床落地",
            "行业标准：AI 辅助诊断框架技术方案入选 3 个省级医疗标准，诊断准确率提升 95%"
          ])
        ]
      ),

      // 安华亿能
      createWorkExperience(
        "安华亿能医疗影像科技",
        "CTO",
        "2012.04 - 2018.09",
        [
          new Paragraph({ text: "核心职责：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "制定公司技术战略，管理 40+ 人研发团队",
            "主导智能影像识别系统架构设计与医疗器械注册"
          ]),
          new Paragraph({ text: "关键成果：", style: "HighlightStyle", spacing: { before: 120 } }),
          createBulletList([
            "技术创新：首创全球颈动脉三维超声诊断系统，斑块自动检测准确率 98.2%",
            "多模态平台：开发 CT/MRI/超声跨模态融合技术，搭建 DICOM 智能分析系统",
            "SaaS 平台：开发云诊所影像 SaaS 平台，完成 130+ 家三甲医院 PACS 系统无缝对接",
            "医疗器械：主导 II 类医疗器械从概念到 NMPA 认证全流程，建立设计控制闭环",
            "智能产线：部署 MES+ 机器视觉质检系统，构建 GMP 体系下 AI 驱动的生产异常预测模型"
          ])
        ]
      ),

      new Paragraph({ children: [new PageBreak()] }),

      // ========== 核心项目经验 ==========
      new Paragraph({ text: "核心项目经验", style: "Heading1" }),

      // AI Agent 系统
      createProjectExperience(
        "AI Agent 系统（药物警戒智能体） | 主导架构设计",
        "2024.01 - 2024.11",
        [
          new Paragraph({ text: "项目背景：构建基于大模型的药物警戒系统，实现 AE/SAE 自动采集、分级、多语言翻译、全球分发", spacing: { before: 120 } }),
          new Paragraph({ text: "技术架构决策：", style: "HighlightStyle", spacing: { before: 80 } }),
          createBulletList([
            "Agent 框架：LangChain（工具集成）+ AutoGen（多 Agent 协作）+ Dify（工作流编排）",
            "RAG 检索：基于 LlamaIndex 实现定向检索，Zep 向量存储 + MemGPT 记忆逻辑控制",
            "决策框架：多 LLM 支持（GPT/Claude/Gemini/DeepSeek/Doubao）+ PDDL 规划算法",
            "提示词工程：PromptPerfect 自动优化 + BERT 语义理解偏差修正"
          ]),
          new Paragraph({ text: "核心成果：", style: "HighlightStyle", spacing: { before: 80 } }),
          createBulletList([
            "完成药物 AE/SAE 自动采集与分级，支持多语言翻译与全球分公司分发",
            "研究数据医学稽查 Agent 定制稽查规则，自动生成稽查报告",
            "系统已上线运行，实现从数据采集到报告生成的全流程自动化"
          ])
        ]
      ),

      // CTMS+EDC 系统
      createProjectExperience(
        "CTMS+EDC 临床试验管理系统 | 架构师",
        "进行中",
        [
          new Paragraph({ text: "项目背景：主导设计临床试验管理系统，符合 ICH GCP、FDA 21 CFR Part 11、CDISC/SDTM 标准", spacing: { before: 120 } }),
          new Paragraph({ text: "技术架构：", style: "HighlightStyle", spacing: { before: 80 } }),
          createBulletList([
            "后端：Node.js/TypeScript + Express.js + Prisma ORM + PostgreSQL",
            "前端：React + Vite + Ant Design + Zustand",
            "核心模块：EdcTemplate、CrfForm、CrfData、AdverseEvent、角色权限、工时管理、项目收支、全流程审批",
            "数据合规：6 类 CSV/JSON 导出功能（CDISC 标准 eCRF 与 SDTM 导出）",
            "系统特性：私有部署 + 多租户架构，支持企业微信集成"
          ]),
          new Paragraph({ text: "当前进展：", style: "HighlightStyle", spacing: { before: 80 } }),
          createBulletList([
            "后端 30+ 模块、前端 21 页面已完成",
            "正在推进 RAG 检索系统构建（文档分词 + 向量库导入）",
            "调研 CDISC/SDTM 标准合规实现，设计 Code Dictionary 映射机制"
          ])
        ]
      ),

      new Paragraph({ children: [new PageBreak()] }),

      // ========== 技术能力矩阵 ==========
      new Paragraph({ text: "技术能力矩阵", style: "Heading1" }),

      createTable([
        ["大模型应用", "Prompt Engineering、RAG、Agent 编排、Function Calling、Skill 框架、LangChain、LlamaIndex、Dify、AutoGen、Zep、MemGPT"],
        ["后端架构", "Node.js/TypeScript、Java、Python、Go、微服务架构、API 网关、BFF 层、Express.js、Spring Boot"],
        ["前端技术", "React、Vue、前端框架升级、Vite、Ant Design、Zustand"],
        ["数据架构", "PostgreSQL、MySQL、MongoDB、Redis、Kafka、Spark、Hadoop、数据中台"],
        ["AI/算法", "Transformer、PyTorch、TensorFlow、RNN、CNN、知识图谱、联邦学习、多模态融合"],
        ["云原生", "Docker、Kubernetes、Jenkins、HPA、边缘计算 K3S、云原生存储"],
        ["医疗合规", "ICH GCP E6(R2)、FDA 21 CFR Part 11、GDPR、CDISC、SDTM、OMOP、CDMP"],
        ["企业应用", "企业微信 API、微信生态、政企 SaaS、私有部署、多租户系统"]
      ], true),

      new Paragraph({ children: [new PageBreak()] }),

      // ========== 教育背景 ==========
      new Paragraph({ text: "教育背景", style: "Heading1" }),
      
      createBulletList([
        "山东大学 | 硕士 · 数据科学与大数据技术 | 2004.07 - 2007.06",
        "北京科技大学 | 本科 · 计算机应用 | 1998.07 - 2002.07"
      ]),

      // ========== 资格证书 ==========
      new Paragraph({ text: "资格证书", style: "Heading1" }),
      
      createBulletList([
        "高级人工智能训练师",
        "高级健康管理师",
        "大学英语四级（读写精通）"
      ]),

      // ========== 附加说明 ==========
      new Paragraph({ text: "附加说明", style: "Heading1" }),
      
      createBulletList([
        "系统重构经验：主导过多次老系统重构（前端框架升级、微服务改造、数据中台建设）",
        "外包管理经验：具备外包运维伙伴服务质量与 SLA 管理实战经验",
        "跨组织协作：40+ 项目涉及多方协作（NMPA/CDE/北京大学/三甲医院/药企/保险公司）",
        "技术标准：参与制定 3+ 项行业标准，技术方案入选 3+ 个省级标准",
        "知识产权：获得 3+ 项发明专利，主导国自然课题、'十三五'国家重点研发计划"
      ])
    ]
  }]
});

// 辅助函数：创建项目经历
function createProjectExperience(title, date, children) {
  return [
    new Paragraph({ 
      children: [
        new TextRun({ text: title, style: "Heading2" }),
        new TextRun({ text: "  ", style: "Heading2" }),
        new TextRun({ text: date, style: "DateStyle" })
      ],
      spacing: { after: 80 }
    }),
    ...children
  ];
}

// 辅助函数：创建工作经历
function createWorkExperience(company, position, date, children) {
  return [
    new Paragraph({ 
      children: [
        new TextRun({ text: company, bold: true, style: "HighlightStyle" }),
        new TextRun({ text: " | ", style: "HighlightStyle" }),
        new TextRun({ text: position, style: "HighlightStyle" })
      ],
      spacing: { before: 120, after: 40 }
    }),
    new Paragraph({ text: date, style: "DateStyle", spacing: { after: 80 } }),
    ...children
  ];
}

// 辅助函数：创建项目经历
function createProjectExperience(title, date, children) {
  return [
    new Paragraph({ 
      children: [
        new TextRun({ text: title, bold: true, style: "HighlightStyle" }),
        new TextRun({ text: "  ", style: "HighlightStyle" }),
        new TextRun({ text: date, style: "DateStyle" })
      ],
      spacing: { before: 120, after: 80 }
    }),
    ...children
  ];
}

// 辅助函数：创建 bullet list
function createBulletList(items) {
  return items.map(item => 
    new Paragraph({
      numbering: { reference: "bullets", level: 0 },
      style: "BulletStyle",
      children: [new TextRun({ text: item, style: "BulletStyle" })]
    })
  );
}

// 辅助函数：创建表格
function createTable(data, hasHeader = false) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: COLORS.BORDER };
  const borders = { top: border, bottom: border, left: border, right: border };
  
  const rows = data.map((row, index) => {
    const isHeader = hasHeader && index === 0;
    return new TableRow({
      children: row.map(cellText => 
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA },
          shading: { 
            fill: isHeader ? "D5E8F0" : "FFFFFF", 
            type: ShadingType.CLEAR 
          },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [
            new Paragraph({
              children: [
                new TextRun({ 
                  text: cellText, 
                  bold: isHeader,
                  color: isHeader ? COLORS.SECONDARY : COLORS.TEXT,
                  font: "Microsoft YaHei",
                  size: 22
                })
              ]
            })
          ]
        })
      )
    });
  });

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [4680, 4680],
    rows,
    spacing: { cell: 100 }
  });
}

// 生成文档
Packer.toBuffer(resumeDoc)
  .then(buffer => {
    const outputPath = path.join('D:', 'doc', '蔡宇衡的简历-AI 技术总监优化版.docx');
    fs.writeFileSync(outputPath, buffer);
    console.log('✅ Word 文档生成成功！');
    console.log('📄 文件路径：' + outputPath);
  })
  .catch(error => {
    console.error('❌ 生成失败:', error);
  });
