import { Suspense } from "react";
import { StockTemplate } from "@/components/stock/StockTemplate";

// The ticker comes from the URL at request time, so the template streams in behind Suspense.
export default function Layout({ children, params }: LayoutProps<"/[locale]/t/[ticker]">) {
  return (
    <Suspense fallback={<div className="h-14 shrink-0 border-b border-line" />}>
      <StockLayout params={params}>{children}</StockLayout>
    </Suspense>
  );
}

async function StockLayout({
  params,
  children,
}: {
  params: LayoutProps<"/[locale]/t/[ticker]">["params"];
  children: React.ReactNode;
}) {
  const { ticker } = await params;
  return <StockTemplate slug={decodeURIComponent(ticker)}>{children}</StockTemplate>;
}
