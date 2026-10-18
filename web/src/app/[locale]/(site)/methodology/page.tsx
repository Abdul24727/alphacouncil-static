import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { MethodologyPage } from "@/components/site/MethodologyPage";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, titled } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/methodology">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "site.methodology" });
  return localizedMetadata(locale, "/methodology", titled(t("title")), t("lead"));
}

export default async function Page({ params }: PageProps<"/[locale]/methodology">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <MethodologyPage locale={locale} />;
}
