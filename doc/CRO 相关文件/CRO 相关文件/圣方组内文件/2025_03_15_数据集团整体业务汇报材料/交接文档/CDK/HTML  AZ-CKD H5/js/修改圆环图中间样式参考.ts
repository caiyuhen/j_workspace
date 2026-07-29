const colorList: { text: string, color: string }[] = [
  { text: '正常', color: '#429D75' },
  { text: '报警', color: '#AB487F' },
  { text: '离线', color: '#959FC8' },
  { text: '运行', color: '#5970DD' },
  { text: '停机', color: '#737373' },
]
const data = dealData.map((item) => {
  const color = colorList.find((vv) => vv?.text === item.name)?.color
  return {
    value: item.value,
    name: item.name,
    itemStyle: { color },
    percent: item.percent,
    label: {
      normal: {
        show: true,
      },
    },
  }
})
const richStyle = {
  normal: {
    color: '#429D75',
    fontFamily: 'MicrosoftYaHei-Bold',
  },
  alarm: {
    color: '#DB599D',
    fontFamily: 'MicrosoftYaHei-Bold',
  },
  work: {
    color: '#5970DD',
    fontFamily: 'MicrosoftYaHei-Bold',
  },
  stop: {
    color: 'rgba(255,255,255,0.45)',
    fontFamily: 'MicrosoftYaHei-Bold',
  },
  outline: {
    color: '#959FC8',
    fontFamily: 'MicrosoftYaHei-Bold',
  },
  value: {
    padding: [0, 8, 0, 8],
  },
}
const option: Partial<EChartOption> = {
  backgroundColor: '#15192D ',
  tooltip: {
    trigger: 'item',
    formatter: '{b} : {c}台',
    backgroundColor: 'rgba(19,26,60,0.85)',
    borderColor: 'rgba(89,112,221,0.45)',
    textStyle: {
      color: 'rgba(255,255,255,0.85)',
    },
    confine: true,
  },
  grid: {
    top: 0,
    left: 0,
  },
  legend: {
          fontSize: 24,
    orient: 'vertical',
    left: 'center',
    bottom: '7%',
    icon: 'circle',
    itemHeight: 8,
    itemWidth: 8,
    textStyle: {
      fontSize: 12,
      rich: richStyle,
    },
    formatter: function (name: string) {
      let tarValue: number = 0
      let percent: string = ''
      for (let i = 0; i < data.length; i++) {
        if (name === data[i].name) {
          tarValue = data[i].value
          percent = data[i].percent
        }
      }
      switch (name) {
        case '正常':
          return (
            '{normal|' +
            name +
            '}' +
            ' ' +
            '{value|' +
            tarValue +
            '台 ' +
            '}' +
            percent +
            '%'
          )
        case '报警':
          return (
            '{alarm|' +
            name +
            '}' +
            ' ' +
            '{value|' +
            tarValue +
            '台 ' +
            '}' +
            percent +
            '%'
          )
        case '运行':
          return (
            '{work|' +
            name +
            '}' +
            ' ' +
            '{value|' +
            tarValue +
            '台 ' +
            '}' +
            percent +
            '%'
          )
        case '停机':
          return (
            '{stop|' +
            name +
            '}' +
            ' ' +
            '{value|' +
            tarValue +
            '台 ' +
            '}' +
            percent +
            '%'
          )
        case '离线':
          return (
            '{outline|' +
            name +
            '}' +
            ' ' +
            '{value|' +
            tarValue +
            '台 ' +
            '}' +
            percent +
            '%'
          )
        default:
          return name + ' ' + tarValue + '台 ' + percent + '%'
      }
    },
  },
  series: [
    {
      name: '设备',
      type: 'pie',
      radius: ['42%', '67%'],
      data: data,
      center: ['50%', '37%'],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
      label: {
        normal: {
          show: false,
          formatter: function () {
            let total: number = 0
            for (let i = 0; i < data.length; i++) {
              total += data[i].value
            }
            return '{total|' + total + '}' + '\n' + '{unit|' + '(台)' + '}'
          },
          position: 'center',
          lineHight: 30,
          rich: {
            total: {
              fontFamily: 'MicrosoftYaHei- Bold',
              fontSize: '20px',
              color: 'rgba(255, 255, 255, 0.85)',
            },
            unit: {
              fontFamily: 'MicrosoftYaHei',
              fontSize: '12',
              color: 'rgba(255, 255, 255, 0.45)',
            },
          },
        },
      },
      labelLine: {
        show: false,
      },
    },
  ],
}
