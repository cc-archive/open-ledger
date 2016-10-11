var webpack = require('webpack');

var PROD = (process.env.NODE_ENV === 'production')

var root = "/openledger/static"

module.exports = [{
  context: __dirname + root + "/js",
  entry: "./index",
  output: {
    path: __dirname + root + "/js/build",
    filename: PROD
      ? 'openledger.min.js'
      : 'openledger.js'
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
