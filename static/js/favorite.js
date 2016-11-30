import 'whatwg-fetch'
var _ = require('underscore')
import * as Cookies from "js-cookie"

import {API_BASE, HOST_PORT, HOST_URL} from './api'

export const toggleFavorite = function (e) {
  e.stopPropagation()
  e.preventDefault()

  var form = e.target.parentNode
  var method = 'PUT'

  const url = API_BASE + 'images/favorite/' + form.elements['identifier'].value
  const csrf = Cookies.get('csrftoken')

  // If they aren't logged in, tell them to do so. We can improve the UI here later.
  if (form.dataset.loggedIn != 'True') {
    alert("Please sign in to save this image to a list.")
    return
  }

  if (form.dataset.isFavorite === true) {
    method = 'DELETE'
  }

  fetch(url, {
    method: method,
    body: JSON.stringify({}),
    credentials: "include",
    headers: {
      "X-CSRFToken": csrf,
      "Content-Type": "application/json"
    }
  })
  .then((response) => {
    if (response.status === 204) { // We removed a favorite
      removeAsFavorite(form)
    }
    else if (response.status === 201 || response.status === 200) {  // We added a favorite
      setAsFavorite(form)
    }
  })
}


export const setAsFavorite = (form) => {
  form.querySelector('button').classList.remove('secondary')
  form.querySelector('button').classList.add('success')
  form.dataset.isFavorite = true
}
export const removeAsFavorite = (form) => {
  form.querySelector('button').classList.remove('success')
  form.querySelector('button').classList.add('secondary')
  form.dataset.isFavorite = false
}


document.addEventListener('DOMContentLoaded', () => {
  var results = document.querySelector('.results')
  let url = API_BASE + 'images/favorites'

  if (results && document.body.dataset.loggedIn === 'true') {
    // Get the list of the users' favorites if they're logged in

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
      let identifiers = new Set()

      for (let fave of json) {
        identifiers.add(fave.image.identifier)
      }

      // For each result, check if the identifier is in the favorites set, and if
      // so update the color of the favorites button
      const imageResults = results.querySelectorAll('.image-result')

      for (let img of imageResults) {
        if (identifiers.has(img.dataset.identifier)) {
          let favoriteButton = img.querySelector('.favorite-button')
          favoriteButton.classList.remove('secondary')
          favoriteButton.classList.add('success')
        }
      }
    })
  }
})
