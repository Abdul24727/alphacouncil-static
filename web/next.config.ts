import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

// FastAPI origin. The browser only ever calls /api/v1/* on this origin.
const API_ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // The floating badge covers the sidebar's language switch; build errors still show as an overlay.
  devIndicators: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${API_ORIGIN}/v1/:path*` }];
  },
};

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

export default withNextIntl(nextConfig);
