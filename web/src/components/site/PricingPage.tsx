import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { Link } from "@/i18n/navigation";
import { getPlans, type Plans } from "@/lib/api/server";
import { ButtonLink, Db, Unavailable, WRAP } from "./ui";

type Props = { locale: string };

export const PAGE_TITLE = "headline text-[clamp(40px,5vw,64px)] leading-none font-extrabold rtl:leading-[1.2]";
export const PAGE_LEAD = "mt-5 max-w-[640px] text-[17px] leading-[1.6] text-text-soft";
export const H2 = "headline text-[clamp(26px,3vw,34px)] leading-tight";

/** /pricing — Free vs Pro, prices from the API's plan configuration (the Moyasar checkout's). */
export async function PricingPage({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.pricing" });
  return (
    <div className={`${WRAP} pt-10 md:pt-16`}>
      <h1 className={PAGE_TITLE}>{t("title")}</h1>
      <p className={PAGE_LEAD}>{t("lead")}</p>
      <Suspense fallback={<PlanColumns plans={undefined} locale={locale} />}>
        <LoadedPlans locale={locale} />
      </Suspense>
      <div className="mt-10 flex flex-col items-start gap-4 text-[15px] text-text-soft">
        <ButtonLink href="/signup">{t("start")}</ButtonLink>
        <p className="max-w-[640px]">{t("payments")}</p>
        <p>
          {t.rich("refunds", {
            link: (c) => (
              <Link href="/legal/refunds" className="text-signal hover:underline">
                {c}
              </Link>
            ),
          })}
        </p>
      </div>
    </div>
  );
}

async function LoadedPlans({ locale }: Props) {
  return <PlanColumns plans={await getPlans()} locale={locale} />;
}

/** plans: undefined while loading (no numbers), null when the API could not answer. */
async function PlanColumns({ plans, locale }: { plans: Plans | null | undefined; locale: string }) {
  const t = await getTranslations({ locale, namespace: "site" });
  const ar = locale === "ar";
  const price = (id: string) => {
    if (plans === undefined) return <span className="block h-6" />;
    const p = plans?.plans.find((x) => x.id === id);
    if (!p) return <Unavailable>{t("unavailable")}</Unavailable>;
    const currency = t.has(`currency.${p.currency}` as "currency.SAR") ? t(`currency.${p.currency}` as "currency.SAR") : p.currency;
    return (
      <p className="text-[20px] text-text" data-plan-price={p.id}>
        {t.rich("pricing.price", { n: (c) => <Db>{c}</Db>, price: String(p.price_sar), currency })}
      </p>
    );
  };
  const name = (id: "free" | "pro") => {
    const p = plans?.plans.find((x) => x.id === id);
    return p ? (ar ? p.name_ar : p.name) : id === "free" ? (ar ? "مجاني" : "Free") : ar ? "برو" : "Pro";
  };
  const freeItems = t.raw("pricing.free.items") as string[];

  return (
    <>
      <div className="mt-12 grid border-t border-line md:grid-cols-2">
        <section className="flex flex-col gap-4 py-8 md:pe-10">
          <h2 className="headline text-[36px] leading-none">{name("free")}</h2>
          {price("free")}
          <p className="text-[16px] text-text">{t("pricing.free.lead")}</p>
          <ul className="flex flex-col text-[15px] text-text-soft">
            {freeItems.map((item) => (
              <li key={item} className="border-t border-line py-2.5">
                {item}
              </li>
            ))}
          </ul>
        </section>
        <section className="flex flex-col gap-4 border-t border-line py-8 md:border-t-0 md:border-s md:ps-10">
          <h2 className="headline text-[36px] leading-none">{name("pro")}</h2>
          {price("pro")}
          <p className="text-[16px] text-text">{t("pricing.pro.lead")}</p>
          <p className="rounded-chip border border-dashed border-line px-3 py-2.5 font-mono text-[12px] text-muted">
            {t("pricing.pro.placeholder")}
          </p>
        </section>
      </div>
      {plans && !plans.checkout_open && (
        <p className="border-y border-line py-3 text-[15px] text-text" data-checkout-closed>
          {t("pricing.checkoutClosed")}
        </p>
      )}
    </>
  );
}
