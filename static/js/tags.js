import 'whatwg-fetch'
var _ = require('underscore')
import * as Cookies from "js-cookie"

import {API_BASE, HOST_PORT, HOST_URL} from './api'
import * as utils from './utils'

export const addTagsForm = function (e) {

  var form = e.target.nextElementSibling

  // If they aren't logged in, tell them to do so. We can improve the UI here later.
  if (document.body.dataset.loggedIn != 'True') {
    alert("Please sign in to add tags to this image.")
    return
  }

  var input = form.querySelector('input[type=text]')

  // Clear any old messages
  for (var msg of document.querySelectorAll('.add-tags-response')) {
    utils.clearResponse(msg)
  }

  form.style.display = 'block'
  form.classList.toggle('pulse')
  form.addEventListener('submit', addTags, false)
  input.focus()

  // Index into the autocomplete selection value
  input.dataset.sel = -1

  // Move through autocomplete, as event capturing
//  input.addEventListener('keydown', navigateAutocomplete, false)

  // Typeahead, as event capturing
//  input.addEventListener('keyup', _.throttle(completeTagsTitle, 1000), false)

  // Add cancel handler last, as bubbling
//  document.body.addEventListener('keydown', cancelTagsModals, false)

  e.stopPropagation()
  e.preventDefault()
}

export const addTags = function(e) {
  const url = API_BASE + 'images/tags'

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
    tag: form.elements["name"].value,
    identifier: form.elements["identifier"].value
  }

  // Don't allow submitting without a tag name if that snuck by the browser
  if (!data.tag) { return }

  var msg = form.nextElementSibling

  utils.showUpdateMessage(msg)
  utils.clearForm(form)

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
    getUserTagsForImage(data.identifier)
    utils.clearResponse(msg)

  })
}


/* Close any open models -- this is called last in the event bubbling chain if no autocomplete actions are in-progress */
const cancelTagsModals = function (e) {
  if (e.keyCode === 27) {
    for (var form of document.querySelectorAll('.add-tags')) {
      utils.clearForm(form)
      utils.clearResponse(msg)
    }
  }
}

/* Get tags for this image and inject an array of tag objects */
export const getUserTagsForImage = (identifier) => {
  let url = API_BASE + 'images/tags/' + identifier

  fetch(url, {
    method: 'GET',
    credentials: "include",
    headers: {
      "Content-Type": "application/json"
    }
  })
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    var userTagsContainer = document.querySelector('.user-tags-container')

    while (userTagsContainer.firstChild) {
      userTagsContainer.removeChild(userTagsContainer.firstChild);
    }
    for (let usertag of json) {
      console.log(usertag)
      let t = document.createElement('span')
      t.innerHTML = usertag.tag.name
      t.classList.add('primary')
      t.classList.add('label')
      userTagsContainer.appendChild(t)
    }
  })
}

document.addEventListener('DOMContentLoaded', () => {
  var detail = document.querySelector('.image-detail')
  if (detail && document.body.dataset.loggedIn === 'True') {
    getUserTagsForImage(detail.dataset.identifier)
  }
})
