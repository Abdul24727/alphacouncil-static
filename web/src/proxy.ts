import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Skip the API proxy, Next internals and static files. Only real file extensions are
  // excluded: ticker slugs such as /t/ADAV.AD or /t/NBB.BH contain dots.
  matcher: "/((?!api|_next|_vercel|.*\\.(?:ico|png|jpe?g|gif|svg|webp|avif|woff2?|ttf|txt|xml|json|map|js|css|webmanifest)$).*)",
};
