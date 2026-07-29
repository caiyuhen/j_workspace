;(function flexible(window, document) {
  function resetFontSize() {
    console.log(
      'document.documentElement.clientWidth',
      document.documentElement.clientWidth
    )
    if (document.documentElement.clientWidth < 640) {
      window.location.href = './mobile.html'
    }
    const size = (document.documentElement.clientWidth / 1920) * 37.5
    document.documentElement.style.fontSize = size + 'px'
  }

  // reset root font size on page show or resize
  window.addEventListener('pageshow', resetFontSize)
  window.addEventListener('resize', resetFontSize)
})(window, document)
