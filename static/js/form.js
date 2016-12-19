/* When a new search is initiated, reset the page counter */
export const resetSearchOnSubmit = (form) => {
  form.elements["page"].value = 1
}

export const showFormElements = (form) => {
  showForm(form)

  // Do the same for the delete form
  var deleteForm = form.nextElementSibling
  if (deleteForm) {
    showForm(deleteForm)
  }

}

const showForm = (form) => {

  for (var el of form.querySelectorAll('input')) {
    el.style.display = 'inherit'
  }
  for (var el of form.querySelectorAll('textarea')) {
    el.style.display = 'inherit'
  }
  for (var el of form.querySelectorAll('label')) {
    el.style.display = 'inherit'
  }
  for (var el of form.querySelectorAll('.form-readonly')) {
    el.style.display = 'none'
  }
}
