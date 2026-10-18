import { setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";
import { googleNotice } from "@/lib/auth-notices";
import type { Locale } from "@/i18n/routing";

export default async function Page({ params, searchParams }: PageProps<"/[locale]/signup">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return (
    // ?next= is request data: the form streams in with it behind Suspense.
    <Suspense fallback={<AuthForm mode="signup" />}>
      <WithNext searchParams={searchParams} />
    </Suspense>
  );
}

async function WithNext({ searchParams }: Pick<PageProps<"/[locale]/signup">, "searchParams">) {
  const { next, google } = await searchParams;
  // Google sign-in comes back with ?google= (api/app/oauth.py); only known values are shown.
  const notice = googleNotice("google_" + google);
  return <AuthForm mode="signup" next={typeof next === "string" ? next : undefined} notice={notice} />;
}
