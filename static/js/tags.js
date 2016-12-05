import 'whatwg-fetch'
var _ = require('underscore')
import * as Cookies from "js-cookie"

import {API_BASE, HOST_PORT, HOST_URL} from './api'

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
