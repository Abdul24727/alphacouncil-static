import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { LegalIndex } from "@/components/site/LegalPages";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, titled } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/legal">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "site.legal" });
  return localizedMetadata(locale, "/legal", titled(t("title")), t("lead"));
}

export default async function Page({ params }: PageProps<"/[locale]/legal">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <LegalIndex locale={locale} />;
}
