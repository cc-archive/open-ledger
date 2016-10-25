import 'whatwg-fetch'

const API_BASE = '/api/v1/'

const HOST_PORT = window.location.port === 80 ? '' : `:${window.location.port}`
const HOST_URL = `${window.location.protocol}//${window.location.hostname}${HOST_PORT}`


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
  form.addEventListener('submit', addToList)

  input.focus()
  input.scrollIntoView()
}

// Create or modify a list, returning the list slug
export const addToList = (e) => {
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

  var status_code

  fetch(url, {
    method: 'PUT',
    body: data
  })
  .then((response) => {
    status_code = response.status_code
    return response.json()
  })
  .then((json) => {
    if (json.hasOwnProperty('slug')) {
      msg.innerHTML = `Your image was saved to <a href="${HOST_URL}/list/${json.slug}">${HOST_URL}/list/${json.slug}</a>`
    }
    else {
      console.log(json)
    }
  })
}
