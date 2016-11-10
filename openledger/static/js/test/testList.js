import 'jsdom-global/register'
import sinon from 'sinon'
import { assert } from 'chai'


import * as list from '../list'

require( "./util" )


describe('checkStatus', () => {
  it('returns the response if a 200 status code is returned', () => {
    const response = {}
    response.status = 200
    assert(response === list.checkStatus(response))
  }),
  it('raises an exception if a non 200 status code is returned', () => {
    const response = {}
    response.status = 404
    assert.throws(() => list.checkStatus(response))
  })
})

describe('clearResponse', () => {
  it('removes any child nodes from the object', () => {
    var r = document.createElement('div')
    r.innerHTML = "children"
    list.clearResponse(r)
    assert('' === r.innerHTML)
  }),
  it('make the object not visible', () => {
    var r = document.createElement('div')
    list.clearResponse(r)
    assert('none' === r.style.display)
  })
})

describe('clearAutocomplete', () => {
  it('removes any child nodes from the object', () => {
    var r = document.createElement('div')
    r.innerHTML = "children"
    list.clearAutocomplete(r)
    assert('' === r.innerHTML)
  })
})

describe('clearForm', () => {
  var form
  beforeEach(() => {
    form = document.createElement('form')
    form.innerHTML = `<form>
      <input type="text" name="title" />
      <div class="autocomplete"></div>
      </form>`
  })
  it('removes child elements from the autocomplete child', () => {
    var auto = form.querySelector('.autocomplete')
    auto.appendChild(document.createElement('li'))
    assert('' != auto.innerHTML)
    list.clearForm(form)
    assert('' === auto.innerHTML)
  }),
  it('resets the form', () => {
    form.elements["title"].value = 'hello'
    list.clearForm(form)
    assert('' === form.elements["title"].value)
  }),
  it('hides the form', () => {
    assert('none' != form.style.display)
    list.clearForm(form)
    assert('none' === form.style.display)
  }),
  it('removes the animation', () => {
    form.classList.add('pulse')
    assert(1 === form.classList.length)
    list.clearForm(form)
    assert(0 === form.classList.length)
  })



})
