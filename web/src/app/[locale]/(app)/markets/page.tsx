import { getTranslations, setRequestLocale } from "next-intl/server";
import { MarketsView } from "@/components/market/MarketsView";
import { WorkHeader } from "@/components/shell/WorkHeader";
import type { Locale } from "@/i18n/routing";

export default async function Page({ params }: PageProps<"/[locale]/markets">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  const t = await getTranslations("pages");
  return (
    <>
      <WorkHeader title={t("markets")} />
      <MarketsView />
    </>
  );
}
