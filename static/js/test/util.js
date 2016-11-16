
var _attr = function(val){
      var out = val.substr(5);
      return out.split("-").map((part, i) => {
        return part.charAt(0).toUpperCase() + part.substr(1);
      }).join("");
    },

    _data = (el) => {
      let atts = el.attributes,
          len = atts.length,
          attr,
          dataDict = [],
          proxy = {},
          dataName
        for (let i=0; i < len; i++){
          attr = atts[i].nodeName;
          if (attr.indexOf("data-") === 0) {
            dataName = _arr(attr);
            if (dataDict.hasOwnProperty(dataName)) {
              dataDict[dataName] = atts[i].nodeValue
              Object.defineProperty(proxy, dataName, {
                get: () => dataDict[dataName],
                set: (val) => {
                  dataDict[dataName] = val
                  el.setAttribute(attr, val)
                }
              })
            }
          }
        }
        return proxy;
    };

Object.defineProperty(global.window.Element.prototype, "dataset", {
  get: function() {
    return _data(this)
  }
})
