var webpack = require('webpack');

var PROD = (process.env.NODE_ENV === 'production')

var root = "/static"

module.exports = [{
  context: __dirname + root + "/js",
  entry: ['whatwg-fetch', "./index"],
  output: {
    path: __dirname + root + "/js/build",
    filename: 'openledger.js',
    vendor: ['photoswipe', 'photoswipe/src/js/ui/photoswipe-ui-default.js']
  },
  module: {
    loaders: [{
        test: /.js/,
        loaders: ['babel-loader?cacheDirectory']
      }, {
        test: /\.json$/,
        loader: 'json'
      }
    ]
  },
  plugins: PROD ? [
    new webpack.optimize.UglifyJsPlugin({
      compress: {
        warnings: false,
        screw_ie8: true
      },
      comments: false
    }),
    new webpack.DefinePlugin({
      "process.env": {
          NODE_ENV: JSON.stringify("production")
      }
    })]
    : [new webpack.DefinePlugin({
        "process.env": {
        NODE_ENV: JSON.stringify("develop")
        }
    })]
  }
];
module.exports[0].plugins.push (new webpack.ProvidePlugin({PhotoSwipe: 'photoswipe', PhotoSwipeUI_Default: './photoswipe-ui-default'}))

