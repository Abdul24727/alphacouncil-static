import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { LegalIndex } from "@/components/site/LegalPages";
import type { Locale } from "@/i18n/routing";

export async function generateMetadata({ params }: PageProps<"/[locale]/legal">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "site.legal" });
  return { title: `${t("title")} · AlphaCouncil`, description: t("lead") };
}

export default async function Page({ params }: PageProps<"/[locale]/legal">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <LegalIndex locale={locale} />;
}
