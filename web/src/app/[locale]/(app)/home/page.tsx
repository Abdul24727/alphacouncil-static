import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { HomeView } from "@/components/market/HomeView";
import { WorkHeader } from "@/components/shell/WorkHeader";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, titled } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/home">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "pages" });
  const m = await getTranslations({ locale, namespace: "meta" });
  return localizedMetadata(locale, "/home", titled(t("home")), m("home"));
}

export default async function Page({ params }: PageProps<"/[locale]/home">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  const t = await getTranslations("pages");
  return (
    <>
      <WorkHeader title={t("home")} />
      <HomeView />
    </>
  );
}
