import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Landing } from "@/components/site/Landing";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, SITE_NAME } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "site.hero" });
  const m = await getTranslations({ locale, namespace: "meta" });
  return localizedMetadata(locale, "/", `${SITE_NAME} · ${m("tagline")}`, t("lead"));
}

export default async function Page({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <Landing locale={locale} />;
}
