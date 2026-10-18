import { setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";
import { googleNotice } from "@/lib/auth-notices";
import type { Locale } from "@/i18n/routing";

export default async function Page({ params, searchParams }: PageProps<"/[locale]/login">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return (
    // ?next= is request data: the form streams in with it behind Suspense.
    <Suspense fallback={<AuthForm mode="login" />}>
      <WithNext searchParams={searchParams} />
    </Suspense>
  );
}

async function WithNext({ searchParams }: Pick<PageProps<"/[locale]/login">, "searchParams">) {
  const { next, error } = await searchParams;
  // Google sign-in comes back with ?error= (api/app/oauth.py); only known values are shown.
  const notice = googleNotice(error);
  return <AuthForm mode="login" next={typeof next === "string" ? next : undefined} notice={notice} />;
}
