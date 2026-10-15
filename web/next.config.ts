import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

// FastAPI origin. The browser only ever calls /api/v1/* on this origin.
const API_ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8000";

// Content Security Policy without nonces: nonces would make every page render per request
// and lose the prerendered shells. Everything is served from this origin (fonts are
// self-hosted by next/font, the API sits behind /api). HSTS is set by nginx with TLS.
const isDev = process.env.NODE_ENV === "development";
const CSP = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' blob: data:",
  "font-src 'self'",
  "connect-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const SECURITY_HEADERS = [
  { key: "Content-Security-Policy", value: CSP },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), usb=()" },
];

const nextConfig: NextConfig = {
  cacheComponents: true,
  poweredByHeader: false,
  experimental: {
    // The /api rewrite drops a proxied response that is silent this long (default 30 s).
    // The Copilot stream also sends keep-alives every 10 s (api/app/copilot/stream.py).
    proxyTimeout: 120_000,
  },
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
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${API_ORIGIN}/v1/:path*` }];
  },
};

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

export default withNextIntl(nextConfig);
