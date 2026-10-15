import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { PricingPage } from "@/components/site/PricingPage";
import type { Locale } from "@/i18n/routing";

export async function generateMetadata({ params }: PageProps<"/[locale]/pricing">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "site.pricing" });
  return { title: `${t("title")} · AlphaCouncil`, description: t("lead") };
}

export default async function Page({ params }: PageProps<"/[locale]/pricing">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <PricingPage locale={locale} />;
}
