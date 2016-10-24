import 'whatwg-fetch'

const API_BASE = '/api/v1/'

// Add an item by identifier to a list. If the list doesn't exist, create it
export const addToList = (identifier, list) => {

}

export const addToListForm = (e) => {
  // Bring up a form to capture a list title from a user
  e.preventDefault()
  var form = e.target.nextElementSibling
  form.style.display = 'block'
  form.addEventListener('submit', createList)

}


// Create a list, returning the list slug
export const createList = (e) => {
  e.preventDefault()
  const url = API_BASE + 'lists'
  var form = new FormData(e.target)

  fetch(url, {
    method: 'POST',
    body: form
  })
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    if (json.hasOwnProperty('slug')) {
      console.log(`Created list "${form.get('title')}" with slug ${json.slug} and image ${form.get('identifier')}`)
    }
    else {
      console.log(json)
    }
  })
}
