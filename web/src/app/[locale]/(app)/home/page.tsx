import { getTranslations, setRequestLocale } from "next-intl/server";
import { HomeView } from "@/components/market/HomeView";
import { WorkHeader } from "@/components/shell/WorkHeader";
import type { Locale } from "@/i18n/routing";

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
