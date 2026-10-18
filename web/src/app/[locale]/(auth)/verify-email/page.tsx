import { setRequestLocale } from "next-intl/server";
import { VerifyEmailView } from "@/components/auth/VerifyEmailView";
import type { Locale } from "@/i18n/routing";

// The emailed link's token is in the fragment (#token=…): the page reads it in the browser.
export default async function Page({ params }: PageProps<"/[locale]/verify-email">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return <VerifyEmailView />;
}
