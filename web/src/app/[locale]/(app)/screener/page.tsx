import { getTranslations, setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { ScreenerView } from "@/components/market/ScreenerView";
import { WorkHeader } from "@/components/shell/WorkHeader";
import type { Locale } from "@/i18n/routing";

export default async function Page({ params, searchParams }: PageProps<"/[locale]/screener">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  const t = await getTranslations("pages");
  return (
    <>
      <WorkHeader title={t("screener")} />
      {/* ?exchange= is request data: it streams in behind Suspense. */}
      <Suspense fallback={<ScreenerView />}>
        <WithExchange searchParams={searchParams} />
      </Suspense>
    </>
  );
}

async function WithExchange({ searchParams }: Pick<PageProps<"/[locale]/screener">, "searchParams">) {
  const ex = (await searchParams).exchange;
  return <ScreenerView initialExchange={typeof ex === "string" ? ex : undefined} />;
}
