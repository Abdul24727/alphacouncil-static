import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

// Same-origin: next.config.ts rewrites /api/v1/* to the FastAPI service.
// Regenerate the types with `npm run gen:api` after changing the API.
export const api = createClient<paths>({ baseUrl: "/api" });

export type TickerHit = components["schemas"]["TickerHit"];
