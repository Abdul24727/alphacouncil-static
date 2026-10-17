import { setRequestLocale } from "next-intl/server";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";
import type { Locale } from "@/i18n/routing";

// The emailed link's token is in the fragment (#token=…): the form reads it in the browser.
export default async function Page({ params }: PageProps<"/[locale]/reset-password">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <ResetPasswordForm />;
}
