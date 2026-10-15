import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { MethodologyPage } from "@/components/site/MethodologyPage";
import type { Locale } from "@/i18n/routing";

export async function generateMetadata({ params }: PageProps<"/[locale]/methodology">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "site.methodology" });
  return { title: `${t("title")} · AlphaCouncil`, description: t("lead") };
}

export default async function Page({ params }: PageProps<"/[locale]/methodology">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <MethodologyPage locale={locale} />;
}
