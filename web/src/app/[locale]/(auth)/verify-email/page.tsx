import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { VerifyEmailView } from "@/components/auth/VerifyEmailView";
import type { Locale } from "@/i18n/routing";
import { privateMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/verify-email">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "auth.verify" });
  return privateMetadata(locale, t("title"));
}

// The emailed link's token is in the fragment (#token=…): the page reads it in the browser.
export default async function Page({ params }: PageProps<"/[locale]/verify-email">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <VerifyEmailView />;
}
