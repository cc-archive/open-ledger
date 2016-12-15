import 'jsdom-global/register'
import sinon from 'sinon'
import { assert } from 'chai'
var fs = require('fs')

import * as forms from '../form'

describe('showForm', () => {
  var form

  beforeEach(() => {

    form = document.createElement('form')
    form.innerHTML = `<form>
      <input type="text" name="title" style="display: none"/>
      <textarea style="display: none"></textarea>
      <div>
        <div class="form-readonly">
          <a>event</a>
        </div>
      </div>
      </form>`

  }),

  it('shows any form field children when clicked', () => {
    form.addEventListener('click', forms.showFormElements)
    assert('none' === form.querySelector('input').style.display)
    assert('none' === form.querySelector('textarea').style.display)
    var a = form.querySelector('a')
    a.click()
    assert('inherit' === form.querySelector('input').style.display)
    assert('inherit' === form.querySelector('textarea').style.display)
  }),

  it('hides any element with the `readonly` class', () => {
    form.addEventListener('click', forms.showFormElements)
    assert('none' != form.querySelector('.form-readonly').style.display)
    var a = form.querySelector('a')
    a.click()
    assert('none' === form.querySelector('.form-readonly').style.display)
  })
})
