import 'whatwg-fetch'
var _ = require('underscore')
import * as Cookies from "js-cookie"

import {API_BASE, HOST_PORT, HOST_URL} from './api'

export const toggleFavorite = function (e) {
  var form = e.target.parentNode

  const url = API_BASE + 'images/favorite/' + form.elements['identifier'].value
  var csrf = Cookies.get('csrftoken')

  // If they aren't logged in, tell them to do so. We can improve the UI here later.
  if (form.dataset.loggedIn != 'True') {
    alert("Please sign in to save this image to a list.")
    return
  }

  var data = {}

  fetch(url, {
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
    console.log(json)
  })

  e.stopPropagation()
  e.preventDefault()
}
