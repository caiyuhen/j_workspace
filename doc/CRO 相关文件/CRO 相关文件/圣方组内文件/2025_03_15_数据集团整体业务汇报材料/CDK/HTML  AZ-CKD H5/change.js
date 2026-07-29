//1、 banner的日期
const bannerTime = '第2期&nbsp;&nbsp;2024年03月04日'

// 2、研究重要里程碑--按照顺序来
const milestoneTimes = {
  //计划时间
  plan: [
    '计划：2023-11-15',
    '计划：2023-10-31',
    '计划：2024-06-14',
    '计划：2026-12-31',
    '计划：2024-03-31',
    '计划：2025-05-31',
    '计划：2026-12-31',
    '计划：2027-01-29',
    '计划：2027-06-01',
  ],
  //实际时间
  reality: ['实际：2023-11-07', '实际：2023-11-28'],
}
// 3、目前全国启动入组进展（A亚组CKD-高蛋白尿）
const evolve = [
  ['计划中心数', 37],
  ['实际启动中心数', 16],
  ['A亚组<br>计划总入组数', 500],
  ['A亚组<br>实际总入组数', 124],
  ['B亚组<br>计划总入组数', 1000],
  ['B亚组<br>实际总入组数', 2],
]
// 4、启动入组转介计划
// 4.1、中心启动
const columnar = {
  columnarX: [
    'Nov-23',
    'Dec-23',
    'Jan-24',
    'Feb-24',
    'Mar-24',
    'Apr-24',
    'May-24',
    'Jun-24',
  ], //中心启动X轴数据更改
  // 中心启动（计划）
  dataAName: '中心启动（计划）',
  dataA: [1, 3, 10, 13, 16, 22, 29, 29],
  // 中心启动（实际）
  dataBName: '中心启动（实际）',
  dataB: [1, 2, 8, 10, 16, , ,],
}
// 4.2、患者入组
const columnarTwo = {
  columnarTwoX: [
    'Nov-23',
    'Dec-23',
    'Jan-24',
    'Feb-24',
    'Mar-24',
    'Apr-24',
    'May-24',
    'Jun-24',
  ], //中心启动X轴数据更改
  // 中心启动（计划）
  dataAName: '患者入组（计划）',
  dataA: [1, 3, 27, 81, 151, 263, 381, 500],
  // 中心启动（实际）
  dataBName: '患者入组（实际）',
  dataB: [2, 2, 27, 41,124 , , ,],
}
// 5、提示上面的时间
const tipsTime = '2024年6月'

// 6、数据录入及数据质控需加强的中心
// 6.1、三个圆环图的颜色
const ringColor = ['#1F8DED', '#C3D831', '#F6B53D']
// 东南大学附属中大医院
const fristRing = {
  all: 184, //应录入
  already: 39, //录入完整
  wait: 145, //待录入
}
// 四川省医学科学院四川省人民医院
const secondRing = {
  all: 1104, //应录入
  already: 120, //录入完整
  wait: 1065, //待录入
}

// 厦门市第五医院
const thirdRing = {
  all: 112, //应录入
  already: 51, //录入完整
  wait: 61, //待录入
}
// 6.2、二个饼状图的颜色
const PieChartColor = ['#1F8DED', '#F6B53D', '#41B3C9', '#135E9F']
// 东南大学附属中大医院
const fristPieChart = {
  all: 23, //质疑总数
  wait: 7, //待回答质疑数
  already: 0, //已回答质疑数
  close: 16, //关闭质疑数
}
// 四川省医学科学院四川省人民医院
const secondPieChart = {
  all: 6, //质疑总数
  wait: 3, //待回答质疑数
  already: 0, //已回答质疑数
  close: 3, //关闭质疑数
}

// 7、问题和注意事项
const firstNote = `

<!--<span class="jsontext_216">本研究使用的eGFR计算方法</span>
<div class="jsontext-group_20 flex-col justify-between">
  <span class="jsonparagraph_8">
    需要使用2009年和2021年的计算器分别进行计算，链接请参考：
    <br />
    2021年版本CKD-EPI（肌酐）计算器链接：
	<a href="http://huodong.medlive.cn/calc_tools/calc/show/2?id=calc-112">
   	 http://huodong.medlive.cn/calc_tools/calc/show/2?id=calc-112
	</a>
    <br />
    2009年版本CKD-EPI（肌酐）计算器链接【注意选择“性别”，统一选择“国际”，人种选择“其他人种”】：
      <a href="https://peppernotes.top/skip/MedTools/319.html">
	 https://peppernotes.top/skip/MedTools/319.html
     </a>
  </span>
  <div class="jsontext-wrapper_83">
    <span class="jsontext_217">⚠️</span>
    <span class="jsontext_218">
      &nbsp;用“CKD-EPI&nbsp;（肌酐）”，不要误点“CKD-EPI&nbsp;（胱抑素C）”等。
    </span>
  </div>
</div>-->
<span class="jsontext_216">知情同意要点</span>	 
<div class="jsontext-group_20 flex-col justify-between">
  <span class="jsonparagraph_8">受试者获益<br/>参加本研究可能没有直接获益，但是本项研究的结果可能加深受试者对慢性肾脏病的医学科学知识的了解<br />
	 受试者风险<br/>可能在将来对相同疾病的患者的治疗带来益处
	 <br />知情同意过程<br />
	 充分并详尽告知本研究及知情同意书内容，签署知情同意书，且研究者在病历中及时、充分记录知情同意过程。<br />
	 本研究创新性的使用了私域群和电子问卷收集模式，还请各注意知情时做好患者的培训工作，告知该问卷的安全性，提醒患者知情后按时完成电子问卷，及在后续随访加强对受试者的管理！
	 </span>
 
</div>	 

`
const secondNote = `
<span class="jsontext_219">
是否能够出具免疫抑制治疗的药物名单供研究者参考？
</span>
<div class="jsontext-group_21 flex-col justify-between">
<span class="jsonparagraph_9">
  第一类，糖皮质激素，是临床中最常用的免疫抑制剂，如氢化可的松、泼尼松；
  <br />
  第二类，细胞毒性药物，如硫唑嘌呤、甲氧蝶呤、环磷酰胺等；
  <br />
  第三类，真菌产物，如环孢素、他克莫司、西罗莫司等；
  <br />
  第四类，免疫细胞单克隆抗体，如CD3单克隆抗体（OKT3）、利妥昔单抗等；
  <br />
  第五类，细胞因子及其受体拮抗剂，如英夫利昔单抗、伊那西普、托珠单抗等。
  <br />
  第六类，中药抑制剂药物，如雷公藤。
</span>
<div class="jsontext-wrapper_84">
  <span class="jsontext_220">⚠️</span>
  <span class="jsontext_221">
    &nbsp;筛选患者时请仔细核对既往使用免疫抑制药物治疗的情况。
  </span>
</div>
</div>
`
// 8、A亚组研究中心进展
const tableData = [
  {
    id: '13001', //序号
    hospital: '东南大学附属中大医院', //研究中心
    name: '刘必成', //PI
    status: '入组', //阶段
    dotColor: '#940683',
    aGroup: '10', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: '0', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13002', //序号
    hospital: '北京大学人民医院', //研究中心
    name: '左力', //PI
    status: '入组', //阶段
    dotColor: '#22D1FF',
    aGroup: '2', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13003', //序号
    hospital: '江苏省人民医院', //研究中心
    name: '毛慧娟', //PI
    status: '启动', //阶段
    dotColor: '#22D1FF',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13004', //序号
    hospital: '上海交通大学医学院附属瑞金医院', //研究中心
    name: '谢静远', //PI
    status: '合同', //阶段
    dotColor: '#F6B53D',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13005', //序号
    hospital: '四川省医学科学院四川省人民医院', //研究中心
    name: '李贵森', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '19', //A亚组入组例数
    aGroupIsShowSun: 'inline-block', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13007', //序号
    hospital: '宁波第二医院', //研究中心
    name: '罗群', //PI
    status: '合同', //阶段
    dotColor: '#940683',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13008', //序号
    hospital: '北京积水潭医院', //研究中心
    name: '张东亮', //PI
    status: '入组', //阶段
    dotColor: '#22D1FF',
    aGroup: '7', //A亚组入组例数
    aGroupIsShowSun: 'inline-block', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13009', //序号
    hospital: '武汉市普爱医院', //研究中心
    name: '董骏武', //PI
    status: '启动', //阶段
    dotColor: '#22D1FF',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13011', //序号
    hospital: '四川大学华西医院', //研究中心
    name: '付平', //PI
    status: '入组', //阶段
    dotColor: '#F6B53D',
    aGroup: '6', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13013', //序号
    hospital: '吉林省人民医院', //研究中心
    name: '王松岩', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '4', //A亚组入组例数
    aGroupIsShowSun: 'inline-block', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13014', //序号
    hospital: '北京大学第一医院', //研究中心
    name: '吕继成', //PI
    status: '启动', //阶段
    dotColor: '#940683',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13015', //序号
    hospital: '中山大学孙逸仙纪念医院', //研究中心
    name: '杨琼琼', //PI
    status: '入组', //阶段
    dotColor: '#22D1FF',
    aGroup: '0', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: '0', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13020', //序号
    hospital: '浙江省台州医院', //研究中心
    name: '徐光标', //PI
    status: '入组', //阶段
    dotColor: '#22D1FF',
    aGroup: '11', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13021', //序号
    hospital: '西安交通大学医学院第一附属医院', //研究中心
    name: '路万虹', //PI
    status: '立项', //阶段
    dotColor: '#F6B53D',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13022', //序号
    hospital: '无锡市人民医院', //研究中心
    name: '王凉', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '16', //A亚组入组例数
    aGroupIsShowSun: 'inline-block', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13023', //序号
    hospital: '重庆医科大学附属第二医院', //研究中心
    name: '廖晓辉', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '10', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13024', //序号
    hospital: '自贡第一人民医院', //研究中心
    name: '郝炎', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '21', //A亚组入组例数
    aGroupIsShowSun: 'inline-block', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13025', //序号
    hospital: '北京清华长庚医院', //研究中心
    name: '李月红', //PI
    status: '合同', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13026', //序号
    hospital: '株洲市中心医院', //研究中心
    name: '彭清丰', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '0', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: '0', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13027', //序号
    hospital: '南华大学附属第一医院', //研究中心
    name: '邓进', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '0', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: '0', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13028', //序号
    hospital: '中南大学湘雅三医院', //研究中心
    name: '易斌', //PI
    status: '合同', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13029', //序号
    hospital: '汕头大学医学院第二附属医院', //研究中心
    name: '周添标', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '11', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: '0', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13030', //序号
    hospital: '宜宾第二人民医院', //研究中心
    name: '张臣丽', //PI
    status: '合同', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13031', //序号
    hospital: '厦门市第五医院', //研究中心
    name: '郝炎', //PI
    status: '入组', //阶段
    dotColor: '#C3D831',
    aGroup: '3', //A亚组入组例数
    aGroupIsShowSun: 'inline-block', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: '0', //中止退出例数
  },
  {
    id: '13032', //序号
    hospital: '武汉市中心医院', //研究中心
    name: '陈文莉', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13033', //序号
    hospital: '温州医科大学附属第一医院', //研究中心
    name: '陈朝生', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13034', //序号
    hospital: '南宁市第一人民医院', //研究中心
    name: '廖兵', //PI
    status: '合同', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13035', //序号
    hospital: '上海第五人民医院', //研究中心
    name: '牛建英', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13036', //序号
    hospital: '西交交通大学第二附属医院', //研究中心
    name: '付荣国', //PI
    status: '立项', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13037', //序号
    hospital: '深圳市第二人民医院', //研究中心
    name: '万启军', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13038', //序号
    hospital: '东莞市人民医院', //研究中心
    name: '李仪', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13039', //序号
    hospital: '淮安市第一人民医院', //研究中心
    name: '陈连花', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13040', //序号
    hospital: '宁海市第一医院', //研究中心
    name: '边学燕', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13041', //序号
    hospital: '武汉大学人民医院', //研究中心
    name: '杨定平', //PI
    status: '立项', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13042', //序号
    hospital: '甘肃省人民医院', //研究中心
    name: '黄文辉', //PI
    status: '伦理', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13043', //序号
    hospital: '海南省第三人民医院', //研究中心
    name: '高敏捷', //PI
    status: '立项', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
  {
    id: '13044', //序号
    hospital: '暨南大学附属第一医院', //研究中心
    name: '刘璠娜', //PI
    status: '立项', //阶段
    dotColor: '#C3D831',
    aGroup: 'NA', //A亚组入组例数
    aGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    bGroup: 'NA', //B亚组入组例数
    bGroupIsShowSun: 'none', // none 不展示 inline-block 展示
    exit: 'NA', //中止退出例数
  },
]
