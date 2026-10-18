import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, titled } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/forgot-password">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "auth.forgot" });
  const m = await getTranslations({ locale, namespace: "meta" });
  return localizedMetadata(locale, "/forgot-password", titled(t("title")), m("forgot"));
}

export default async function Page({ params }: PageProps<"/[locale]/forgot-password">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <ForgotPasswordForm />;
}
