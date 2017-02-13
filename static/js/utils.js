export const detectIE = () => {
  var ua = window.navigator.userAgent
  var msie = ua.indexOf('MSIE ')
  if (msie > 0) {
    // IE 10 or older => return version number
    return parseInt(ua.substring(msie + 5, ua.indexOf('.', msie)), 10)
  }

  var trident = ua.indexOf('Trident/')
  if (trident > 0) {
    // IE 11 => return version number
    var rv = ua.indexOf('rv:')
    return parseInt(ua.substring(rv + 3, ua.indexOf('.', rv)), 10)
  }

  var edge = ua.indexOf('Edge/')
  if (edge > 0) {
    // Edge (IE 12+) => return version number
    return parseInt(ua.substring(edge + 5, ua.indexOf('.', edge)), 10)
  }
  // other browser
  return false
}

export const clearAutocomplete = (autocomplete) => {
  autocomplete.innerHTML = ''
}

export const clearResponse = (response) => {
  response.style.display = 'none'
  response.innerHTML = ''
}

export const checkStatus = (response) => {
  if (response.status >= 200 && response.status < 300) {
    return response
  }
  else {
    var error = new Error(response.statusText)
    error.response = response
    throw error
  }
}

export const clearForm = (form) => {
  var autocomplete = form.querySelector('.autocomplete')
  clearAutocomplete(autocomplete)
  form.reset()
  form.style.display = 'none'
  form.classList.remove('pulse')
  var input = form.querySelector('input[type=text]')
  input.dataset.sel = -1  // Reset the autocomplete pointer

}

export const showUpdateMessage = (msg) => {
  msg.style.display = 'block'
  msg.innerHTML = "Saving..."
}
