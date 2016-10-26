import 'whatwg-fetch'
var _ = require('underscore')

const API_BASE = '/api/v1/'

const HOST_PORT = window.location.port === 80 ? '' : `:${window.location.port}`
const HOST_URL = `${window.location.protocol}//${window.location.hostname}${HOST_PORT}`


export const addToListForm = function (e) {
  // Bring up a form to capture a list title from a user
  var form = e.target.nextElementSibling
  var input = form.querySelector('input[type=text]')

  // Clear the old message if it's still there
  var msg = form.nextElementSibling
  msg.style.display = 'none'

  form.style.display = 'block'
  form.classList.toggle('pulse')
  form.addEventListener('submit', addToList.bind(form), false)

  input.focus()
  input.scrollIntoView()
  input.addEventListener('keyup', _.throttle(completeListTitle.bind(form), 1000), false)
}

// Return autocomplete results for lists by title
export const completeListTitle = function () {
  const form = this
  const input = form.elements["title"]
  const identifier = form.elements["identifier"]

  // Don't do anything if we haven't typed anything except clear the autocomplete list
  if (!input.value) {
    var autocomplete = input.nextElementSibling
    autocomplete.innerHTML = ''
    return
  }
  const url = API_BASE + 'lists?title=' + encodeURIComponent(input.value)

  fetch(url, {
    method: 'GET'
  })
  .then(checkStatus)
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    // Create an autocomplete field beneath the input
    var autocomplete = input.nextElementSibling
    autocomplete.innerHTML = ''

    for (var list of json.lists) {
      var item = document.createElement('li')
      var a = document.createElement('a')
      a.innerHTML = list.title
      item.appendChild(a)
      var meta = document.createElement('span')
      meta.innerHTML = ` with ${list.images.length} image${list.images.length != 1 ? 's' : ''}`
      item.appendChild(meta)
      autocomplete.appendChild(item)

      item.addEventListener('click', selectAndAddToList.bind(form, list.slug))
    }
  })
  .catch(function(error) {
    if (error.response.status != 404) {
      console.log(error)
    }
  })
}

// Select a node from the autocomplete list and send that
export const selectAndAddToList = function(slug) {
  const url = API_BASE + 'list/images'
  const form = this

  var data = new FormData(form)

  var msg = form.nextElementSibling
  showUpdateMessage(msg)

  clearForm(form)

  data.set('slug', slug)

  fetch(url, {
    method: 'POST',
    body: data
  })
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    msg.innerHTML = `Your image was added to <a href="${HOST_URL}/list/${json.slug}">${HOST_URL}/list/${json.slug}</a>`
    form.reset()
  })
}

// Create or modify a list, returning the list slug
export const addToList = function(e) {
  const url = API_BASE + 'lists'

  e.preventDefault()

  var form = this
  var data = new FormData(form)
  var msg = form.nextElementSibling

  showUpdateMessage(msg)
  clearForm(form)

  fetch(url, {
    method: 'PUT',
    body: data
  })
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    msg.innerHTML = `Your image was saved to <a href="${HOST_URL}/list/${json.slug}">${HOST_URL}/list/${json.slug}</a>`
    form.reset()
  })
}

const showUpdateMessage = (msg) => {
  msg.style.display = 'block'
  msg.innerHTML = "Saving..."
}
const clearForm = (form) => {
  var autocomplete = form.querySelector('.autocomplete')
  autocomplete.innerHTML = ''

  form.style.display = 'none'
  form.classList.remove('pulse')
}

function checkStatus(response) {

  if (response.status >= 200 && response.status < 300) {
    return response
  } else {
    var error = new Error(response.statusText)
    error.response = response
    throw error
  }
}
