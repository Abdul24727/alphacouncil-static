import { CheckIcon } from "@radix-ui/react-icons";
import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";
import { Link } from "@/i18n/navigation";
import { googleNotice } from "@/lib/auth-notices";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, titled } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/signup">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "auth" });
  const m = await getTranslations({ locale, namespace: "meta" });
  return localizedMetadata(locale, "/signup", titled(t("signupTitle")), m("signup"));
}

export default async function Page({ params, searchParams }: PageProps<"/[locale]/signup">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return (
    <div data-auth-wide className="grid gap-10 md:grid-cols-[minmax(0,24rem)_minmax(0,1fr)] md:gap-14">
      {/* ?next= is request data: the form streams in with it behind Suspense. */}
      <Suspense fallback={<AuthForm mode="signup" />}>
        <WithNext searchParams={searchParams} />
      </Suspense>
      <FreePlanPanel locale={locale} />
    </div>
  );
}

/**
 * What the free account gives (design fix 8, owner 2026-11-21): beside the form on desktop,
 * under it on a phone. The lines are the Free plan's own from /pricing (site.pricing.free),
 * so the two pages cannot drift apart.
 */
async function FreePlanPanel({ locale }: { locale: string }) {
  const t = await getTranslations({ locale, namespace: "site.pricing" });
  const ta = await getTranslations({ locale, namespace: "auth" });
  const items = t.raw("free.items") as string[];
  return (
    <aside aria-labelledby="free-plan-title" className="border-t border-line pt-8 md:border-t-0 md:border-s md:ps-14 md:pt-1" data-free-plan>
      <h2 id="free-plan-title" className="headline text-[22px] leading-tight">
        {ta("freeTitle")}
      </h2>
      <p className="mt-2 text-text-soft">{t("free.lead")}</p>
      <ul className="mt-5 flex flex-col">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2.5 border-t border-line py-2.5 text-[14px] leading-snug text-text">
            <CheckIcon aria-hidden className="mt-0.5 size-4 shrink-0 text-muted" />
            {item}
          </li>
        ))}
      </ul>
      <Link href="/pricing" className="mt-4 inline-block text-signal hover:underline">
        {ta("comparePlans")}
      </Link>
    </aside>
  );
}

async function WithNext({ searchParams }: Pick<PageProps<"/[locale]/signup">, "searchParams">) {
  const { next, google } = await searchParams;
  // Google sign-in comes back with ?google= (api/app/oauth.py); only known values are shown.
  const notice = googleNotice("google_" + google);
  return <AuthForm mode="signup" next={typeof next === "string" ? next : undefined} notice={notice} />;
}
