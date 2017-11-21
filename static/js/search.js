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
    var adv_search = document.getElementById ("toggle_advanced_search");
    if (adv_search) { 
        adv_search.addEventListener ('click', function () { 
            var filters = document.querySelector (".search-filters")
            if (filters.classList.contains ('hide')) {
                filters.classList.remove ("hide");
                this.innerText = 'Hide advanced filters';
            } else {
                filters.classList.add ("hide");
                this.innerText = 'Advanced search';
            }
            
        })
    }
})
