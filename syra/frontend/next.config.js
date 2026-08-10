const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Keep Turbopack / tracing rooted in this app when other lockfiles exist on the machine
  turbopack: {
    root: path.join(__dirname),
  },
}

module.exports = nextConfig
