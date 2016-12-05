import 'jsdom-global/register'
import sinon from 'sinon'
import { assert } from 'chai'

import * as favorite from '../favorite'

require( "./test-utils" )

describe('setAsFavorite', () => {
  var form
  beforeEach(() => {
    form = document.createElement('form')
    form.innerHTML = `<form>
      <input type="hidden" name="identifier" />
      <button></button>
      </form>`
  })
  it('sets/removes the classes of the form in added-mode', () => {
    favorite.setAsFavorite(form)
    var button = form.querySelector('button')
    assert(button.classList.contains('success'))
    assert(!button.classList.contains('secondary'))
  })
})

describe('removeAsFavorite', () => {
  var form
  beforeEach(() => {
    form = document.createElement('form')
    form.innerHTML = `<form>
      <input type="hidden" name="identifier" />
      <button></button>
      </form>`
  })

  it('sets/removes the classes of the form in removed-mode', () => {
    favorite.removeAsFavorite(form)
    var button = form.querySelector('button')
    assert(!button.classList.contains('success'))
    assert(button.classList.contains('secondary'))
  })
})
