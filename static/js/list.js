import 'whatwg-fetch'
var _ = require('underscore')
import * as Cookies from "js-cookie"

import {API_BASE, HOST_PORT, HOST_URL} from './api'
 
/* Bring up a form to capture a list title from a user */
export const addToListForm = function (e) {

  var form = e.target.nextElementSibling

  // If they aren't logged in, tell them to do so. We can improve the UI here later.
  if (form.dataset.loggedIn != 'True') {
    alert("Please sign in to save this image to a list.")
    return
  }

  var input = form.querySelector('input[type=text]')

  // Clear any old messages
  for (var msg of document.querySelectorAll('.add-to-list-response')) {
    clearResponse(msg)
  }

  form.style.display = 'block'
  form.classList.toggle('pulse')
  form.addEventListener('submit', addToList, false)
  input.focus()

  // Index into the autocomplete selection value
  input.dataset.sel = -1

  // Move through autocomplete, as event capturing
  input.addEventListener('keydown', navigateAutocomplete, false)

  // Typeahead, as event capturing
  input.addEventListener('keyup', _.throttle(completeListTitle, 1000), false)

  // Add cancel handler last, as bubbling
  document.body.addEventListener('keydown', cancelListModals, false)

  e.stopPropagation()
  e.preventDefault()
}

/* DELETE an image from a List */
export const deleteImageFromList = function (e) {
  if (confirm("Are you sure you want to delete this image from this list?")) {
    e.preventDefault()
    var form = e.target.parentNode
    const url = API_BASE + 'lists/' + form.elements["slug"].value

    var data = {
      images: [
        {identifier: form.elements["identifier"].value}
      ]
    }
    var csrf = Cookies.get('csrftoken')

    fetch(url, {
      method: 'DELETE',
      body: JSON.stringify(data),
      credentials: "include",
      headers: {
        "X-CSRFToken": csrf,
        "Content-Type": "application/json"
      }
    })
    .then(checkStatus)
    .then((response) => {
      // If we were successful, delete this item out of the DOM
      var result = form.parentNode.parentNode
      result.classList.add('animated')
      result.classList.add('zoomOut')
    })
  }
}

/* Use keyboard controls to move through an autocomplete list */
export const navigateAutocomplete = function (e) {
  // Is the autocomplete open?
  const autocomplete = this.nextElementSibling

  // Is autocomplete empty?
  if (autocomplete.children.length === 0) {
    // If so, did the user hit ESC? They were probably trying to close the
    // whole modal, if so
    if (e.keyCode === 27) {
      clearForm(this.parentNode)
      clearResponse(this.parentNode.nextElementSibling)
      e.stopPropagation()
    }
    return
  }

  var offset // The offset we'll apply to the index
  var index = parseInt(this.dataset.sel)

  if (e.keyCode === 38) { // Up
    offset = index > 0 ? -1 : 0
    e.stopPropagation()
  }
  else if (e.keyCode === 40) { // Down
    offset = index < autocomplete.children.length - 1 ? 1 : 0
    e.stopPropagation()
  }
  else if (e.keyCode === 27) { // ESC
    autocomplete.innerHTML = ''
    e.stopPropagation()
    return
  }
  else {
    return // We're not interested in their typing
  }

  e.preventDefault()

  // Clear earlier values, if any
  var selected = autocomplete.querySelectorAll('.hover')
  for (var s of selected) {
    s.classList.remove('hover')
  }

  index += offset

  selected = autocomplete.children[index]
  if (selected) {
    selected.classList.add('hover')
  }
  this.dataset.sel = index
}

/* Return autocomplete results for lists by title */
export const completeListTitle = function (e) {
  const form = this.parentNode
  const input = form.elements["title"]
  const identifier = form.elements["identifier"]
  const autocomplete = input.nextElementSibling

  // Don't do anything if we haven't typed anything except clear the autocomplete list
  if (!input.value) {
    autocomplete.innerHTML = ''
    return
  }

  // Don't go further if the user typed arrow keys or ESC
  if (e.keyCode === 37 || e.keyCode === 38 || e.keyCode === 39 || e.keyCode === 40 ||
      e.keyCode === 27) {
    return
  }

  const url = API_BASE + 'autocomplete/lists?title=' + encodeURIComponent(input.value)

  fetch(url, {
    method: 'GET',
    credentials: 'include'
  })
  .then(checkStatus)
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    // Create an autocomplete field beneath the input
    var autocomplete = input.nextElementSibling
    autocomplete.innerHTML = ''

    for (var list of json) {
      var item = document.createElement('li')
      var a = document.createElement('a')
      a.innerHTML = list.title
      item.appendChild(a)
      var meta = document.createElement('span')
      if (list.hasOwnProperty('images')) {
        meta.innerHTML = ` with ${list.images.length} image${list.images.length != 1 ? 's' : ''}`
      }
      item.appendChild(meta)

      // Add select events so we can call these with keyboard controls too
      item.addEventListener('mouseover', selectItemAutocomplete)
      item.addEventListener('mouseleave', function() { this.classList.remove('hover')})
      item.dataset.slug = list.slug
      autocomplete.appendChild(item)

      item.addEventListener('click', selectAndAddToList.bind(form, list.slug))
    }
  })
}

/* Visually indicate which item has been selected either via keyboard or mouse/hover */
export const selectItemAutocomplete = function() {
  this.classList.add('hover')
}

/* On Submit of the form, create a new List and add any images in the form to it */
export const selectAndAddToList = function(slug) {
  const url = API_BASE + 'lists/' + slug
  const form = this

  var data = {
    images: [
      {identifier: form.elements["identifier"].value}
    ]
  }

  var msg = form.nextElementSibling

  showUpdateMessage(msg)
  clearForm(form)

  var csrf = Cookies.get('csrftoken')

  fetch(url, {
    method: 'PUT',
    body: JSON.stringify(data),
    credentials: "include",
    headers: {
      "X-CSRFToken": csrf,
      "Content-Type": "application/json"
    }
  })
  .then(checkStatus)
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    successMessage(msg, json.slug, json.title)
  })
}

/* Update (POST/PUT) a new image into an existing List */
export const addToList = function(e) {
  const url = API_BASE + 'lists'

  e.preventDefault()

  var form = this

  // Was the autocomplete open with a selection when this happened?
  // If so, use that selection rather than whatever was typed in the box
  let selected = form.querySelector('.autocomplete .hover')
  if (selected) {
    let send = selectAndAddToList.bind(form)
    send(selected.dataset.slug)
    return
  }

  var data = {
    title: form.elements["title"].value,
    images: [
      {identifier: form.elements["identifier"].value}
    ]
  }

  // Don't allow submitting without a title if that snuck by the browser
  if (!data.title) {
    return
  }

  var msg = form.nextElementSibling

  showUpdateMessage(msg)
  clearForm(form)

  var csrf = Cookies.get('csrftoken')

  fetch(url, {
    method: 'POST',
    body: JSON.stringify(data),
    credentials: "include",
    headers: {
      "X-CSRFToken": csrf,
      "Content-Type": "application/json"
    }
  })
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    if (json.slug) {
      fetch(url + '/' + json.slug, {
        method: 'PUT',
        body: JSON.stringify(data),
        credentials: "include",
        headers: {
          "X-CSRFToken": csrf,
          "Content-Type": "application/json"
        }
      })
      .then((response) => {
        return response.json()
      })
      .then((json) => {
        successMessage(msg, json.slug, json.title)
      })
    }
  })
}

export const showUpdateMessage = (msg) => {
  msg.style.display = 'block'
  msg.innerHTML = "Saving..."
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

/* Show a message when the user has successfully added an image to a list */
export const successMessage = (msg, slug, title) => {
  msg.innerHTML = `<span class="badge success">✓</span>
  Your image was saved to <a href="${HOST_URL}/list/${slug}">${title}</a>`
  msg.classList.add('animated')
  msg.classList.add('pulse')
}

export const deleteConfirm = function (e) {
  // Before deleting a List, confirm
  if (!confirm("Are you sure you want to permanently delete this List?")) {
    e.preventDefault()
    return
  }
}

/* Close any open models -- this is called last in the event bubbling chain if no autocomplete actions are in-progress */
const cancelListModals = function (e) {
  if (e.keyCode === 27) {
    for (var form of document.querySelectorAll('.add-to-list')) {
      clearForm(form)
      clearResponse(form.nextElementSibling)
    }
  }
}
