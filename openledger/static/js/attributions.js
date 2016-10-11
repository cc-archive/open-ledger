
const clipped = (e) => {
  var btn = e.trigger
  var txt = btn.innerHTML

  btn.classList.toggle('animated')
  btn.classList.toggle('bounce')
  btn.innerHTML = "Copied!"

  e.clearSelection()
  window.setTimeout(() => {
    btn.classList.remove('bounce')
    btn.classList.remove('animated')
    btn.innerHTML = txt
  }, 1500)
}

const attributions = (clipboard) => {
  clipboard.on('success', clipped)
}

export default attributions
