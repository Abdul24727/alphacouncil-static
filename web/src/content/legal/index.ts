// The legal documents, copied verbatim from the old site by scripts/import-legal.py.
// Do not edit the JSON by hand: change the signed-off source and re-run the import.
import aiAr from "./ai-financial-disclaimer.ar.json";
import aiEn from "./ai-financial-disclaimer.en.json";
import cookiesAr from "./cookies.ar.json";
import cookiesEn from "./cookies.en.json";
import merchantAr from "./merchant.ar.json";
import merchantEn from "./merchant.en.json";
import privacyAr from "./privacy.ar.json";
import privacyEn from "./privacy.en.json";
import refundsAr from "./refunds.ar.json";
import refundsEn from "./refunds.en.json";
import termsAr from "./terms.ar.json";
import termsEn from "./terms.en.json";

export const LEGAL_DOCS = ["terms", "privacy", "refunds", "cookies", "ai-financial-disclaimer"] as const;
export type LegalDoc = (typeof LEGAL_DOCS)[number];

export type LegalDocument = {
  title: string;
  version: string;
  effective: string;
  updated: string | null;
  operator: string;
  translationNote: string | null;
  toc: { href: string; label: string }[];
  canonicalHash: string | null;
  html: string;
  blocks: number;
};

const DOCS: Record<"en" | "ar", Record<LegalDoc, LegalDocument>> = {
  en: { terms: termsEn, privacy: privacyEn, refunds: refundsEn, cookies: cookiesEn, "ai-financial-disclaimer": aiEn },
  ar: { terms: termsAr, privacy: privacyAr, refunds: refundsAr, cookies: cookiesAr, "ai-financial-disclaimer": aiAr },
};

const MERCHANT = { en: merchantEn, ar: merchantAr };

export function isLegalDoc(doc: string): doc is LegalDoc {
  return (LEGAL_DOCS as readonly string[]).includes(doc);
}

export function legalDocument(locale: string, doc: LegalDoc): LegalDocument {
  return DOCS[locale === "ar" ? "ar" : "en"][doc];
}

export function merchantInfo(locale: string): string[] {
  return MERCHANT[locale === "ar" ? "ar" : "en"].html;
}
