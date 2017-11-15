import Masonry from 'masonry-layout'
var imagesLoaded = require('imagesloaded')
var PhotoSwipe = require ('photoswipe')

import * as utils from './utils'
import Clipboard from 'clipboard'
import * as favorite from './favorite'

const columnWidth = 210
const gutter = 5 

const init = (urls) => {
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
window.addEventListener('load', () => {
    const isIE = utils.detectIE()
    var results = document.querySelector('.results')

    if (results) {
        var spinner = document.querySelector('.loading-spinner')
        if (document.querySelector('.image-result')) {
            // shows the spinner in the hope that it will be hidden once the images have loaded
            spinner.style.display = 'block'
        }

        var imgLoad = imagesLoaded('.results')
        //APARENTLY, images.length counts every image on the page, not only the ones in .results
        var lightBox, shown = false;

        imgLoad.on('always', () => {
            // detect which image is broken
            // add images' url to array so we can create a gallery with next/prev.
            var urls = [];
            for (var i=0, len=imgLoad.images.length; i < len; i++) {
                var image = imgLoad.images[i]
                if (!image.isLoaded && !isIE && image.img.dataset && image.img.dataset.title) {
                    // lets hide only the ones that were supposed to be included in the results page.
                    let parent = image.img.parentNode.parentNode.parentNode
                    parent.style.display = 'none'
                } else if (image.img.dataset && image.img.dataset.title) {
                    var captionFn = function () { 
                        // function that duplicates the data_container and add the data for each picture.
                        return function (item, element, isFake) {
                            if (!isFake) { 
                                while (element.firstChild) {
                                    element.removeChild (element.firstChild);
                                }
                                try {
                                    var x = document.querySelector (".not_caption .data_container").cloneNode (true);
                                    x.className += " show";
                                    element.appendChild (x);
                                } catch (e) { }
                                if (i !== undefined) { 
                                    for (var d in item.data) {
                                        var m = document.querySelector('.data_container.show .' + d);
                                        if (m) {
                                            if (d == 'foreign_landing_url') {
                                                m.href = item.data [d];
                                            } else if (d == 'provider') {
                                                m.href = item.data ['provider_url'];
                                                m.innerText = item.data ['provider_name'];
                                            } else if (d == 'license') {
                                                //UGLIEST code ever but we dont have license_version in ES so we have to do this. >:@
                                                var license = item.data [d].toLowerCase (), with_cc = true, buttons = [],segments = license.split ('-');
                                                if (license == 'cc0' || license == 'pdm') with_cc = false; 

                                                if (with_cc) {
                                                    buttons.push ('/static/images/cc.svg');
                                                }
                                                for (var b in segments) {
                                                    buttons.push ('/static/images/' + segments [b] + '.svg')
                                                }
                                                for (var b in buttons) {
                                                    var el = document.createElement ("IMG");
                                                    el.src = buttons [b];
                                                    el.title = buttons[b].toUpperCase ();
                                                    m.appendChild (el);
                                                }
                                            } else {
                                                m.innerText = item.data [d];
                                            }
                                        }
                                    }
                                }
                                return true;
                            } else {
                                var x = document.createElement ("DIV");
                                x.className = "data_container fake";
                                element.appendChild (x);
                            }
                            return false;
                        }
                    }
                    var fn = function (idx) { 
                        return function (e) { 
                            //first and foremost let's stop propagation and default click actions.
                            e.preventDefault ();
                            e.stopPropagation ();

                            try {
                                //Init the gallery.
                                lightBox = new PhotoSwipe (document.querySelectorAll('.pswp')[0], PhotoSwipeUI_Default, urls, {index: idx, addCaptionHTMLFn: captionFn (), shareEl: false, listEl: true, favEl: true, attrEl: true});
                                lightBox.listen ('gettingData', function (index, item) {
                                    // we use this so we don't have to know the image size beforehand.
                                    var i = index;
                                    if (item.w < 1 || item.h < 1) {
                                        var img = new Image ();
                                        img.onload = function () { 
                                            item.w = this.width;
                                            item.h = this.height;

                                            lightBox.invalidateCurrItems ();
                                            lightBox.updateSize (true);
                                        }
                                        img.src = item.src;
                                    }
                                    //TODO: set favorite status here

                                });
                                lightBox.init ();
                            } catch (e) { }

                            // Connect buttons
                            // Copy attribution text
                            // TODO: add HTML option
                            var copy = document.querySelector(".pswp .pswp__button--attribution");
                            var clipboardText = new Clipboard (copy, {
                                text: function () {
                                    var idx = lightBox.getCurrentIndex (), data = urls [idx].data;
                                    return data.title + " by " + data.creator + " is licensed under " + data.license.toUpperCase ();
                                }
                            });
                            clipboardText.on ("success", function (e) { 
                                e.trigger.classList.toggle ('done');

                                window.setTimeout(function () {
                                    e.trigger.classList.remove ('done');
                                }, 1500)
                            })

                            //Toggle the favorite status


                            var fav = document.querySelector(".pswp .pswp__button--favorite");

                            fav.addEventListener ('click', function (e) { 
                                fav.classList.add ('waiting');
                                // first we need to fetch the current item, the data and identifier to then fetch the form that contains the fav status
                                var idx = lightBox.getCurrentIndex (), data = urls [idx].data;
                                var form = document.querySelector("[data-identifier='"+data.identifier+"'] form.add-to-favorite"), isFav = form.dataset['is-favorite'];
                                favorite.toggleFavoriteWithForm (form, (isFav) => { 
                                   fav.classList.remove ('waiting');

                                   if (isFav) { 
                                       fav.classList.add ('is_fav')
                                   } else { 
                                       fav.classList.remove ('is_fav')
                                   }

                                })

                            });
                            var list = document.querySelector(".pswp .pswp__button--list");
                            list.addEventListener ('click', function (e) { 
                                list.classList.add ('waiting');
                                var idx = lightBox.getCurrentIndex (), data = urls [idx].data;
                                var formBtn = document.querySelector("[data-identifier='"+data.identifier+"'] .add-to-list-container button");
                                formBtn.click ();
                            });

                        }
                    }
                    image.img.addEventListener ('click', fn (urls.length));
                    var w = 0, h = 0;
                    urls.push ({src: image.img.dataset.url, w: w, h: h, data: image.img.dataset, title: image.img.dataset.title});
                }
            }
            spinner.style.display = 'none'
            results.style.visibility = 'visible'

            init()
        })
    }

})
