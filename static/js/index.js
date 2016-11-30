import Clipboard from 'clipboard'
import attributions from './attributions'

import * as list from './list'
import * as form from './form'
import * as grid from './grid'
import * as favorite from './favorite'

const init = () => {
  var clipboardText = new Clipboard('.clipboard-sel-text')
  var clipboardHTML = new Clipboard('.clipboard-sel-html', {
      text: () => {
        const htmlBlock = document.querySelector('.attribution')
        return htmlBlock.innerHTML
      }
  })
  attributions(clipboardText)
  attributions(clipboardHTML)
}

document.addEventListener('DOMContentLoaded', () => {
  init()
})

window.openledger = {}
window.openledger.list = list
window.openledger.form = form
window.openledger.grid = grid
window.openledger.favorite = favorite
