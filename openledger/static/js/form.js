
export const showForm = function(e) {
  var form = e.target.parentNode.parentNode.parentNode

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
