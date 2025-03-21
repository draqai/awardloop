const webpack = require('webpack');

module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/socket.io': {  // Add this section for Socket.IO support
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true  // Important for WebSocket connections
      }
    }
  },
  configureWebpack: {
    resolve: {
      fallback: {
        "url": require.resolve("url/"),
        "os": require.resolve("os-browserify/browser"),
        "https": require.resolve("https-browserify"),
        "http": require.resolve("stream-http"),
        "crypto": require.resolve("crypto-browserify"),
        "stream": require.resolve("stream-browserify"),
        "buffer": require.resolve("buffer/"),
        "assert": require.resolve("assert/")
      }
    },
    plugins: [
      new webpack.ProvidePlugin({
        Buffer: ['buffer', 'Buffer'],
        process: 'process/browser'
      })
    ]
  }
}