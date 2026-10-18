import { setRequestLocale } from "next-intl/server";
import { CheckoutView } from "@/components/billing/CheckoutView";
import type { Locale } from "@/i18n/routing";

export default async function Page({ params }: PageProps<"/[locale]/checkout">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <CheckoutView />;
}
