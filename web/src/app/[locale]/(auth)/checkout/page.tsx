import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { CheckoutView } from "@/components/billing/CheckoutView";
import type { Locale } from "@/i18n/routing";
import { privateMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/checkout">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "checkout" });
  return privateMetadata(locale, t("title"));
}

export default async function Page({ params }: PageProps<"/[locale]/checkout">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <CheckoutView />;
}
