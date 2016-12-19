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

    assert('none' === form.querySelector('input').style.display)
    assert('none' === form.querySelector('textarea').style.display)
    forms.showFormElements(form)
    assert('inherit' === form.querySelector('input').style.display)
    assert('inherit' === form.querySelector('textarea').style.display)
  }),

  it('hides any element with the `readonly` class', () => {
    assert('none' != form.querySelector('.form-readonly').style.display)
    forms.showFormElements(form)
    assert('none' === form.querySelector('.form-readonly').style.display)
  })
})
