// 全局的替换

window.addEventListener('load', () => {
  let bar001, bar002, pie001, pie002, pie003, pie004, pie005
  const main001 = document.querySelector('#main001')
  const main002 = document.querySelector('#main002')
  const main003 = document.querySelector('#main003')
  const main004 = document.querySelector('#main004')
  const main005 = document.querySelector('#main005')
  const main006 = document.querySelector('#main006')
  const main007 = document.querySelector('#main007')
  function mobile() {
    const box15 = document.querySelector('.box_15')

    main001.style.width = box15.clientWidth + 'px'
    main001.style.height = box15.clientWidth.toFixed(2) + 'px'

    main002.style.width = box15.clientWidth + 'px'
    main002.style.height = box15.clientWidth.toFixed(2) + 'px'

    main003.style.width = (box15.clientWidth / 1.8).toFixed(2) + 'px'
    main003.style.height = (box15.clientWidth / 1.8).toFixed(2) + 'px'

    main004.style.width = (box15.clientWidth / 1.8).toFixed(2) + 'px'
    main004.style.height = (box15.clientWidth / 1.8).toFixed(2) + 'px'

    main005.style.width = (box15.clientWidth / 1.8).toFixed(2) + 'px'
    main005.style.height = (box15.clientWidth / 1.8).toFixed(2) + 'px'

    main006.style.width = (box15.clientWidth / 1.8).toFixed(2) + 'px'
    main006.style.height = (box15.clientWidth / 1.8).toFixed(2) + 'px'

    main007.style.width = (box15.clientWidth / 1.8).toFixed(2) + 'px'
    main007.style.height = (box15.clientWidth / 1.8).toFixed(2) + 'px'
  }

  ;(function flexible(window, document) {
    function resetFontSize() {
      const size = (document.documentElement.clientWidth / 750) * 37.5
      document.documentElement.style.fontSize = size + 'px'
      console.log(
        'document.documentElement.clientWidth',
        document.documentElement.clientWidth
      )
      if (document.documentElement.clientWidth > 640) {
        window.location.href = './index.html'
      }
      bar001(mobile)
      bar002(mobile)
      pie001(mobile)
      pie002(mobile)
      pie003(mobile)
      pie004(mobile)
      pie005(mobile)
    }

    // reset root font size on page show or resize
    window.addEventListener('pageshow', resetFontSize)
    window.addEventListener('resize', resetFontSize)
  })(window, document)
  const richStyle = {
    blueColor: {
      color: '#1F8DED',
      fontFamily: 'MicrosoftYaHei-Bold',
      fontSize: 24,
      fontWeight: 'bold',
    },
    blackColorBig: {
      color: '#333333',
      fontFamily: 'MicrosoftYaHei-Bold',
      fontSize: 12,
    },
    blackColor: {
      color: '#333333',
      fontFamily: 'MicrosoftYaHei-Bold',
      fontSize: 12,
    },
  }
  // 全局的替换
  ;(function () {
    const bannerTimeDom = document.querySelector('.bannerTime')
    if (bannerTimeDom) bannerTimeDom.innerHTML = bannerTime

    for (let i = 0; i < 10; i++) {
      const plan = document.querySelector(`.plan00${i + 1}`)
      if (plan) plan.innerHTML = milestoneTimes.plan[i]
    }
    for (let i = 0; i < 2; i++) {
      const reality = document.querySelector(`.reality00${i + 1}`)
      if (reality) reality.innerHTML = milestoneTimes.reality[i]
    }
    for (let i = 0; i < 6; i++) {
      const evolveDom = document.querySelector(`.evolve00${i + 1}`)
      if (evolveDom) {
        const evolveList = evolveDom.children
        if (evolveList[0]) evolveList[0].innerHTML = evolve[i][1]
        if (evolveList[1]) evolveList[1].innerHTML = evolve[i][0]
      }
    }
    const tipsTimeDom = document.querySelector('.tipsTime')
    if (tipsTimeDom) tipsTimeDom.innerHTML = tipsTime

    const firstNoteDom = document.querySelector('.firstNote')
    if (firstNoteDom) firstNoteDom.innerHTML = firstNote
    const secondNoteDom = document.querySelector('.secondNote')
    if (secondNoteDom) secondNoteDom.innerHTML = secondNote

    const tbodyList = document.querySelector('.tbodyList')
    let str = ''
    for (let i = 0; i < tableData.length; i++) {
      const ele = tableData[i]
      str += `<tr>
    <td colspan="1">${ele.id}</td>
    <td colspan="3">${ele.hospital}</td>
    <td colspan="1">${ele.name}</td>
    <td colspan="1"><span style="background: ${ele.dotColor};"  class="dot"></span>${ele.status}</td>
    <td colspan="2"><span style="display: ${ele.aGroupIsShowSun};"  class="sun"></span> ${ele.aGroup}</td>
    <td colspan="2"><span style="display: ${ele.bGroupIsShowSun};"  class="sun"></span> ${ele.bGroup}</td>
    <td colspan="2">${ele.exit}</td>
  </tr>`
    }
    if (tbodyList) tbodyList.innerHTML = str
  })()
  // 回到顶部 点击侧边栏加上样式
  ;(function () {
    const backTop = document.querySelector('#backTop')
    const uMenu = document.querySelector('.u-menu')
    const image2 = document.querySelector('.image_2')
    const slideHover = document.querySelector('.slideHover')
    backTop.addEventListener('click', function () {
      window.scrollTo(0, 0)
    })
    image2.addEventListener('click', function (e) {
      console.log('🚀 ~ e.target:', e.target)
      uMenu.classList.toggle('show')
      slideHover.classList.toggle('show')
    })
  })()

  // 柱状图 2个
  bar001 = function (fn) {
    var chartDom = document.getElementById('main001')

    if (!chartDom) return false
    fn && fn()

    var myChart = echarts.init(chartDom)
    var option

    option = {
      legend: {
        data: [columnar.dataAName, columnar.dataBName],
        bottom: '5%',
      },
      color: ['#1F8DED', '#135E9F'],
      xAxis: [
        {
          type: 'category',
          data: columnar.columnarX,
        },
      ],
      yAxis: [
        {
          type: 'value',
        },
      ],
      series: [
        {
          name: columnar.dataAName,
          type: 'bar',
          data: columnar.dataA,
          label: {
            show: true,
            position: 'top',
          },
        },
        {
          name: columnar.dataBName,
          type: 'bar',
          data: columnar.dataB,
          label: {
            show: true,
            position: 'top',
          },
        },
      ],
    }

    option && myChart.setOption(option)
  }
  bar002 = function (fn) {
    var chartDom = document.getElementById('main002')
    if (!chartDom) return false
    fn && fn()

    var myChart = echarts.init(chartDom)
    var option

    option = {
      legend: {
        data: [columnarTwo.dataAName, columnarTwo.dataBName],
        bottom: '5%',
      },
      color: ['#F6B53D', '#940683'],
      xAxis: [
        {
          type: 'category',
          data: columnarTwo.columnarTwoX,
        },
      ],
      yAxis: [
        {
          type: 'value',
        },
      ],
      series: [
        {
          name: columnarTwo.dataAName,
          type: 'bar',
          data: columnarTwo.dataA,
          label: {
            show: true,
            position: 'top',
          },
        },
        {
          name: columnarTwo.dataBName,
          type: 'bar',
          data: columnarTwo.dataB,
          label: {
            show: true,
            position: 'top',
          },
        },
      ],
    }

    option && myChart.setOption(option)
  }
  // 圆环图 3个
  pie001 = function (fn) {
    var chartDom = document.getElementById('main003')
    if (!chartDom) return false
    fn && fn()

    var myChart = echarts.init(chartDom)
    const passVal = ((fristRing.already / fristRing.all) * 100).toFixed(2)
    var option = {
      color: ringColor,
      series: [
        {
          type: 'pie',
          radius: ['60%', '95%'], // 设置环形图的内外半径
          data: [
            { value: fristRing.all, name: fristRing.all },
            { value: fristRing.already, name: fristRing.already },
            { value: fristRing.wait, name: fristRing.wait },
          ],
          label: {
            show: true,
            position: 'inside',
            color: '#ffffff',
            fontSize: 12,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
      legend: {
        orient: 'vertical',
        left: 'center',
        top: '40%',
        icon: 'none',
        itemHeight: 8,
        itemWidth: 8,
        textStyle: {
          fontSize: 24,
          rich: richStyle,
        },
        formatter: function (name) {
          // if (name == fristRing.all) return `${passVal}%\n录入完成率`
          if (name == fristRing.all)
            return `{blueColor|${passVal}}{blackColor|%}\n{blackColorBig|录入完成率}`
          // if (name == fristRing.all) return '{blueColor|' + passVal + '}' + ' ' + '{blackColor|' + '%\n' + '录入完成率' + '}'
        },
      },
      // graphic: {
      //   type: 'text',
      //   left: 'center',
      //   top: '43%', // 调整 top 的值以改变文本在圆环上的位置
      //   style: {
      //     text: `${((fristRing.already / fristRing.all) * 100).toFixed(
      //       2
      //     )}%\n录入完成率`,
      //     textAlign: 'center',
      //     textVerticalAlign: 'middle',
      //     fontSize: 24,
      //     fill: '#000', // 文本颜色
      //   },
      // },
    }

    myChart.setOption(option)
  }
  pie002 = function (fn) {
    var chartDom = document.getElementById('main004')
    if (!chartDom) return false
    fn && fn()

    var myChart = echarts.init(chartDom)
    const passVal = ((secondRing.already / secondRing.all) * 100).toFixed(2)
    var option = {
      color: ringColor,
      series: [
        {
          type: 'pie',
          radius: ['60%', '95%'], // 设置环形图的内外半径
          data: [
            { value: secondRing.all, name: secondRing.all },
            { value: secondRing.already, name: secondRing.already },
            { value: secondRing.wait, name: secondRing.wait },
          ],
          label: {
            show: true,
            position: 'inside',
            color: '#ffffff',
            fontSize: 12,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
      legend: {
        orient: 'vertical',
        left: 'center',
        top: '40%',
        icon: 'none',
        itemHeight: 8,
        itemWidth: 8,
        textStyle: {
          fontSize: 24,
          rich: richStyle,
        },
        formatter: function (name) {
          if (name == secondRing.all)
            return `{blueColor|${passVal}}{blackColor|%}\n{blackColorBig|录入完成率}`
        },
      },
    }

    myChart.setOption(option)
  }
  pie003 = function (fn) {
    var chartDom = document.getElementById('main005')
    if (!chartDom) return false
    fn && fn()

    var myChart = echarts.init(chartDom)
    const passVal = ((thirdRing.already / thirdRing.all) * 100).toFixed(2)
    var option = {
      color: ringColor,
      series: [
        {
          type: 'pie',
          radius: ['60%', '95%'], // 设置环形图的内外半径
          data: [
            { value: thirdRing.all, name: thirdRing.all },
            { value: thirdRing.already, name: thirdRing.already },
            { value: thirdRing.wait, name: thirdRing.wait },
          ],
          label: {
            show: true,
            position: 'inside',
            color: '#ffffff',
            fontSize: 12,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
      legend: {
        orient: 'vertical',
        left: 'center',
        top: '40%',
        icon: 'none',
        itemHeight: 8,
        itemWidth: 8,
        textStyle: {
          fontSize: 24,
          rich: richStyle,
        },
        formatter: function (name) {
          if (name == thirdRing.all)
            return `{blueColor|${passVal}}{blackColor|%}\n{blackColorBig|录入完成率}`
        },
      },
    }

    myChart.setOption(option)
  }
  // 饼状图 2个
  pie004 = function (fn) {
    // const a001 = 4 // 质疑总数
    // const a002 = 2 // 待回答质疑数
    // const a003 = 0 // 已回答质疑数
    // const a004 = 2 // 关闭质疑数
    var chartDom = document.getElementById('main006')
    if (!chartDom) return false
    fn && fn()

    var myChart = echarts.init(chartDom)
    var option

    option = {
      // color: ['#1F8DED', '#F6B53D', '#41B3C9', '#135E9F'],
      radius: '50%',
      series: [
        {
          name: 'Access From',
          type: 'pie',
          radius: 80,
          data: [
            {
              value: fristPieChart.all,
              name: fristPieChart.all,
              itemStyle: { color: PieChartColor[0] },
            },
            {
              value: fristPieChart.wait,
              name: fristPieChart.wait,
              itemStyle: { color: PieChartColor[1] },
            },
            {
              value: fristPieChart.already,
              name: fristPieChart.already,
              itemStyle: { color: PieChartColor[2] },
            },
            {
              value: fristPieChart.close,
              name: fristPieChart.close,
              itemStyle: { color: PieChartColor[3] },
            },
          ],
          label: {
            show: true,
            position: 'inside',
            color: '#ffffff',
            fontSize: 12,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    }

    option && myChart.setOption(option)
  }
  pie005 = function (fn) {
    // const a001 = 4 // 质疑总数
    // const a002 = 2 // 待回答质疑数
    // const a003 = 0 // 已回答质疑数
    // const a004 = 2 // 关闭质疑数
    var chartDom = document.getElementById('main007')
    if (!chartDom) return false
    fn && fn()

    var myChart = echarts.init(chartDom)
    var option

    option = {
      // color: ['#1F8DED', '#F6B53D', '#41B3C9', '#135E9F'],
      radius: '50%',
      series: [
        {
          name: 'Access From',
          type: 'pie',
          radius: 80,
          data: [
            {
              value: secondPieChart.all,
              name: secondPieChart.all,
              itemStyle: { color: PieChartColor[0] },
            },
            {
              value: secondPieChart.wait,
              name: secondPieChart.wait,
              itemStyle: { color: PieChartColor[1] },
            },
            {
              value: secondPieChart.already,
              name: secondPieChart.already,
              itemStyle: { color: PieChartColor[2] },
            },
            {
              value: secondPieChart.close,
              name: secondPieChart.close,
              itemStyle: { color: PieChartColor[3] },
            },
          ],
          label: {
            show: true,
            position: 'inside',
            color: '#ffffff',
            fontSize: 12,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    }

    option && myChart.setOption(option)
  }
})
