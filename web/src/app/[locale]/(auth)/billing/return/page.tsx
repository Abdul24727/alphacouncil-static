import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { ReturnView } from "@/components/billing/ReturnView";
import type { Locale } from "@/i18n/routing";
import { privateMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/billing/return">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "checkout" });
  return privateMetadata(locale, t("title"));
}

export default async function Page({ params }: PageProps<"/[locale]/billing/return">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  // ?id= is request data: the view reads it in the browser, behind Suspense.
  return (
    <Suspense fallback={null}>
      <ReturnView />
    </Suspense>
  );
}
