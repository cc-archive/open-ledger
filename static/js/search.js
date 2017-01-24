document.addEventListener('DOMContentLoaded', () => {

  var workTypes = document.querySelectorAll('.work-type')
  for (let workType of workTypes) {
    let typeSelector = workType.querySelector('input[name="work_types"]')
    let subtype = workType.querySelectorAll('li input')
    // If typeSelectorPhotos is clicked, select all its children
    typeSelector.addEventListener('click', () => {
        for (let st of subtype) {
          st.checked = typeSelector.checked
        }
    })

  }
})
