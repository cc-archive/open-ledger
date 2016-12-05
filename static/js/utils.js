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
