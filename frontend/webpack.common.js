const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin')
const webpack = require('webpack')

module.exports = {
    entry: './src/index.js',
    output: {
        filename: 'main.js',
        path: path.resolve(__dirname, 'dist'),
    },
    devServer: {
        static: {
          directory: path.join(__dirname, 'dist'),
        },
        compress: true,
        port: 9000,
    },
    plugins: [
        new HtmlWebpackPlugin({
            filename: 'index.html',
            template: 'src/index.ejs',
            inject: 'body',
            templateParameters: {
            }
        }),
        new webpack.EnvironmentPlugin({
          DEBUG: false,
          WOFF_ID: 'test id',
          USER_SET_API_URL: 'user set api url',
        })
    ]
};

