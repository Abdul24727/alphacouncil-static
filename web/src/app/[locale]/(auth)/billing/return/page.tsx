import { setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { ReturnView } from "@/components/billing/ReturnView";
import type { Locale } from "@/i18n/routing";

export default async function Page({ params }: PageProps<"/[locale]/billing/return">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  // ?id= is request data: the view reads it in the browser, behind Suspense.
  return (
    <Suspense fallback={null}>
      <ReturnView />
    </Suspense>
  );
}
