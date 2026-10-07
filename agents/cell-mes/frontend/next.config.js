/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: "/production/scheduler",
        destination: "/scheduler",
        permanent: true,
      },
    ];
  },
};

module.exports = nextConfig;
