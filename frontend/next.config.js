/** @type {import('next').NextConfig} */
const nextConfig = {
  skipTrailingSlashRedirect: true,
  typescript: {
    ignoreBuildErrors: false,
  },
}

module.exports = nextConfig
