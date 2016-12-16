import Masonry from 'masonry-layout'
var imagesLoaded = require('imagesloaded')

const columnWidth = 210
const gutter = 10

const init = () => {
  var grid = document.querySelector('.grid')

  if (grid) {
    new Masonry(grid, {
      itemSelector: '.grid-item',
      columnWidth: columnWidth,
      gutter: gutter,
      fitWidth: true
    })
  }

  // Also grid for other provider results; this is kind of blah
  var grid1 = document.querySelector('.grid1')
  var grid2 = document.querySelector('.grid2')
  var grid3 = document.querySelector('.grid3')
  var grid4 = document.querySelector('.grid4')

  if (grid1) {
    new Masonry(grid1, { itemSelector: '.grid-item', columnWidth: columnWidth, gutter: gutter })
  }
  if (grid2) {
    new Masonry(grid2, { itemSelector: '.grid-item', columnWidth: columnWidth, gutter: gutter })
  }
  if (grid3) {
    new Masonry(grid3, { itemSelector: '.grid-item', columnWidth: columnWidth, gutter: gutter })
  }
  if (grid4) {
    new Masonry(grid4, { itemSelector: '.grid-item', columnWidth: columnWidth, gutter: gutter })
  }

}

document.addEventListener('DOMContentLoaded', () => {
  var results = document.querySelector('.results')
  if (results) {
    var spinner = document.querySelector('.loading-spinner')
    spinner.style.display = 'block'

    var imgLoad = imagesLoaded('.results')
    imgLoad.on('always', () => {
      // detect which image is broken
      for (var i=0, len=imgLoad.images.length; i < len; i++) {
        var image = imgLoad.images[i]
        if (!image.isLoaded) {
          let parent = image.img.parentNode.parentNode.parentNode.parentNode
          parent.style.display = 'none'
        }
      }
      spinner.style.display = 'none'
      results.style.visibility = 'visible'
      init()
    })
  }
})
