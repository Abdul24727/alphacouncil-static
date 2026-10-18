import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { PricingPage } from "@/components/site/PricingPage";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, titled } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/pricing">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "site.pricing" });
  return localizedMetadata(locale, "/pricing", titled(t("title")), t("lead"));
}

export default async function Page({ params }: PageProps<"/[locale]/pricing">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <PricingPage locale={locale} />;
}
