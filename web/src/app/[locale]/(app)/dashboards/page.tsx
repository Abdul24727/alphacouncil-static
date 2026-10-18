import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { DashboardsView } from "@/components/dashboards/DashboardsView";
import { WorkHeader } from "@/components/shell/WorkHeader";
import type { Locale } from "@/i18n/routing";
import { privateMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/dashboards">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "pages" });
  return privateMetadata(locale, t("dashboards"));
}

export default async function Page({ params }: PageProps<"/[locale]/dashboards">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  const t = await getTranslations("pages");
  return (
    <>
      <WorkHeader title={t("dashboards")} />
      <DashboardsView />
    </>
  );
}
