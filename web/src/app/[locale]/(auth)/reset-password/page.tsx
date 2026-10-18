import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";
import type { Locale } from "@/i18n/routing";
import { privateMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/reset-password">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "auth.reset" });
  return privateMetadata(locale, t("title"));
}

// The emailed link's token is in the fragment (#token=…): the form reads it in the browser.
export default async function Page({ params }: PageProps<"/[locale]/reset-password">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <ResetPasswordForm />;
}
