import 'whatwg-fetch'

const API_BASE = '/api/v1/'

// Add an item by identifier to a list. If the list doesn't exist, create it
export const addToList = (identifier, list) => {
  // TODO
}

export const addToListForm = (e) => {
  // Bring up a form to capture a list title from a user
  e.preventDefault()
  var form = e.target.nextElementSibling
  var input = form.querySelector('input[type=text]')

  // Clear the old message if it's still there
  var msg = form.nextElementSibling
  msg.style.display = 'none'

  form.style.display = 'block'
  form.classList.toggle('pulse')
  form.addEventListener('submit', createList)

  input.focus()
  input.scrollIntoView()
}


// Create a list, returning the list slug
export const createList = (e) => {
  const url = API_BASE + 'lists'

  e.preventDefault()

  var data = new FormData(e.target)
  var form = e.target

  form.style.display = 'none'

  setTimeout(() => {
    form.classList.toggle('pulse')
    form.classList.toggle('bounceOut')
    form.reset()
  }, 1000)

  var msg = e.target.nextElementSibling
  msg.style.display = 'block'
  msg.innerHTML = "Saving..."

  fetch(url, {
    method: 'POST',
    body: data
  })
  .then((response) => {
    return response.json()
  })
  .then((json) => {
    if (json.hasOwnProperty('slug')) {
      console.log(`Created list "${data.get('title')}" with slug ${json.slug} and image ${data.get('identifier')}`)
      msg.innerHTML = `Your image was saved to <a href="/lists/${json.slug}">${data.get('title')}</a>`
    }
    else {
      console.log(json)
    }
  })
}
