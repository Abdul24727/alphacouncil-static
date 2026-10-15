import { Suspense } from "react";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { WorkHeader } from "@/components/shell/WorkHeader";

// The ticker comes from the URL at request time, so it streams in behind Suspense.
export default function Page({ params }: PageProps<"/[locale]/t/[ticker]">) {
  return (
    <Suspense fallback={<WorkHeader title="" />}>
      <StockPage params={params} />
    </Suspense>
  );
}

async function StockPage({ params }: Pick<PageProps<"/[locale]/t/[ticker]">, "params">) {
  const { locale, ticker } = await params;
  return (
    <PlaceholderPage
      locale={locale}
      page="stock"
      phase={2}
      subtitle={<span className="num text-muted">{decodeURIComponent(ticker)}</span>}
    />
  );
}
