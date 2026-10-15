// Template names in the order every list shows them (sidebar page, landing, /templates).
// Kept out of the "use client" views so server components can read the array itself.
export const TEMPLATES = ["tadawul-stock", "earnings-season", "dividend-hunter", "sector-vs-sector"] as const;
export type TemplateName = (typeof TEMPLATES)[number];

/** Where each template opens: the stock template opens on Saudi Aramco. */
export function templateHref(name: TemplateName) {
  return name === "tadawul-stock" ? "/t/2222" : `/templates/${name}`;
}
