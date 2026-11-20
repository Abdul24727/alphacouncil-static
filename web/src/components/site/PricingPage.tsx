import { CheckIcon, ChevronDownIcon } from "@radix-ui/react-icons";
import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { Link } from "@/i18n/navigation";
import { getPlans, type Plans } from "@/lib/api/server";
import { ButtonLink, Db, Unavailable, WRAP } from "./ui";

type Props = { locale: string };

export const PAGE_TITLE = "headline text-[clamp(40px,5vw,64px)] leading-none font-extrabold rtl:leading-[1.2]";
export const PAGE_LEAD = "mt-5 max-w-[640px] text-[17px] leading-[1.6] text-text-soft";
export const H2 = "headline text-[clamp(26px,3vw,34px)] leading-tight";

/**
 * /pricing — Free vs Pro row by row (design fix 3, owner 2026-11-21), prices from the API's
 * plan configuration (the Moyasar checkout's). The rows are the plans' own feature lines
 * (site.pricing.free/pro.items) word for word: Free's lines are in both plans ("Everything in
 * Free, plus"), Pro's only in Pro. The FAQ answers reuse strings the site already states.
 */
export async function PricingPage({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.pricing" });
  return (
    <div className={`${WRAP} pt-10 md:pt-16`}>
      <h1 className={PAGE_TITLE}>{t("title")}</h1>
      <p className={PAGE_LEAD}>{t("lead")}</p>
      <Suspense fallback={<PlanTable plans={undefined} locale={locale} />}>
        <LoadedPlans locale={locale} />
      </Suspense>
      <div className="mt-8 flex flex-col items-start gap-3 text-[15px] text-text-soft">
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
      <Faq locale={locale} />
      <div className="mt-12">
        <ButtonLink href="/signup">{t("start")}</ButtonLink>
      </div>
    </div>
  );
}

async function LoadedPlans({ locale }: Props) {
  return <PlanTable plans={await getPlans()} locale={locale} />;
}

/** Pro's column is tinted panel grey and topped with the signal colour (BRAND.md tokens). */
const PRO_TINT = "bg-panel";

/** plans: undefined while loading (no numbers), null when the API could not answer. */
async function PlanTable({ plans, locale }: { plans: Plans | null | undefined; locale: string }) {
  const t = await getTranslations({ locale, namespace: "site" });
  const ar = locale === "ar";
  const price = (id: string) => {
    if (plans === undefined) return <span className="block h-6" />;
    const p = plans?.plans.find((x) => x.id === id);
    if (!p) return <Unavailable>{t("unavailable")}</Unavailable>;
    const currency = t.has(`currency.${p.currency}` as "currency.SAR") ? t(`currency.${p.currency}` as "currency.SAR") : p.currency;
    return (
      <p className="text-[13px] leading-snug text-text sm:text-[18px]" data-plan-price={p.id}>
        {t.rich("pricing.price", { n: (c) => <Db>{c}</Db>, price: String(p.price_sar), currency })}
      </p>
    );
  };
  const name = (id: "free" | "pro") => {
    const p = plans?.plans.find((x) => x.id === id);
    return p ? (ar ? p.name_ar : p.name) : id === "free" ? (ar ? "مجاني" : "Free") : ar ? "برو" : "Pro";
  };
  const freeItems = t.raw("pricing.free.items") as string[];
  const proItems = t.raw("pricing.pro.items") as string[];
  const rows: [string, boolean][] = [...freeItems.map((i): [string, boolean] => [i, true]), ...proItems.map((i): [string, boolean] => [i, false])];
  const yes = t("pricing.included");
  const no = t("pricing.notIncluded");

  return (
    <>
      <table className="mt-12 w-full table-fixed border-collapse" data-plan-table>
        <caption className="sr-only">{t("pricing.compare")}</caption>
        <colgroup>
          <col />
          <col className="w-[28%] md:w-[22%]" />
          <col className="w-[28%] md:w-[22%]" />
        </colgroup>
        <thead>
          <tr className="align-top">
            <th scope="col" className="border-b border-line text-start font-normal">
              <span className="sr-only">{t("pricing.feature")}</span>
            </th>
            <th scope="col" className="border-b border-line px-2 py-5 text-start font-normal sm:px-5">
              <PlanHead name={name("free")} price={price("free")} lead={t("pricing.free.lead")}>
                <ButtonLink href="/signup" size="sm">
                  {t("pricing.start")}
                </ButtonLink>
              </PlanHead>
            </th>
            <th
              scope="col"
              className={`border-t-2 border-b border-t-signal border-b-line px-2 py-5 text-start font-normal sm:px-5 ${PRO_TINT}`}
              data-plan-pro
            >
              <PlanHead name={name("pro")} price={price("pro")} lead={t("pricing.pro.lead")}>
                {plans?.checkout_open && (
                  <ButtonLink href="/checkout" size="sm">
                    {t("pricing.getPro")}
                  </ButtonLink>
                )}
              </PlanHead>
            </th>
          </tr>
        </thead>
        <tbody className="text-[14px] sm:text-[15px]">
          {rows.map(([item, inFree]) => (
            <tr key={item} className="border-b border-line align-top">
              <th scope="row" className="py-3 pe-3 text-start font-normal leading-snug text-text-soft">
                {item}
              </th>
              <td className="px-2 py-3 sm:px-5">
                <Mark on={inFree} yes={yes} no={no} />
              </td>
              <td className={`px-2 py-3 sm:px-5 ${PRO_TINT}`}>
                <Mark on yes={yes} no={no} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {/* Until the checkout opens, every account has the Pro features (early access). */}
      {plans && !plans.checkout_open && (
        <p className="border-b border-line py-3 text-[15px] text-text" data-checkout-closed>
          {t("pricing.checkoutClosed")}
        </p>
      )}
    </>
  );
}

function PlanHead({ name, price, lead, children }: { name: string; price: React.ReactNode; lead: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2">
      <h2 className="headline text-[22px] leading-none sm:text-[34px]">{name}</h2>
      {price}
      {/* Too long for a phone's narrow column; the rows below say the same. */}
      <p className="hidden text-[14px] leading-snug text-text-soft md:block">{lead}</p>
      {children}
    </div>
  );
}

/** A check or a muted dash, with words for screen readers. */
function Mark({ on, yes, no }: { on: boolean; yes: string; no: string }) {
  return on ? (
    <span className="inline-flex text-text">
      <CheckIcon aria-hidden className="size-5" />
      <span className="sr-only">{yes}</span>
    </span>
  ) : (
    <span className="text-muted">
      <span aria-hidden>—</span>
      <span className="sr-only">{no}</span>
    </span>
  );
}

/**
 * Questions people ask before paying. Every answer is a fact the site or the app already
 * states, mostly in the same strings, so the two cannot drift apart.
 */
async function Faq({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.pricing" });
  const tc = await getTranslations({ locale, namespace: "copilot" });
  const tk = await getTranslations({ locale, namespace: "checkout" });
  const ts = await getTranslations({ locale, namespace: "settings" });
  const tn = await getTranslations({ locale, namespace: "nav" });
  const tf = await getTranslations({ locale, namespace: "site.footer" });
  // The Copilot's limits are the plans' own lines (the line that names the Copilot).
  const copilotLine = (items: string[]) => items.find((i) => i.includes(tc("title")));
  const freeCopilot = copilotLine(t.raw("free.items") as string[]);
  const proCopilot = copilotLine(t.raw("pro.items") as string[]);
  const refunds = t.rich("refunds", {
    link: (c) => (
      <Link href="/legal/refunds" className="text-signal hover:underline">
        {c}
      </Link>
    ),
  });

  const items: [string, React.ReactNode][] = [[t("faq.card.q"), t("faq.card.a")]];
  if (freeCopilot && proCopilot) {
    items.push([
      t("faq.copilot.q"),
      <ul key="copilot" className="flex flex-col gap-1">
        <li>
          <span className="font-semibold text-text">{t("faq.copilot.free")}</span> {freeCopilot}
        </li>
        <li>
          <span className="font-semibold text-text">{t("faq.copilot.pro")}</span> {proCopilot}
        </li>
      </ul>,
    ]);
  }
  items.push(
    [
      t("faq.cancel.q"),
      <>
        {t("faq.cancel.renews")} {tk("cancelAnytime")} {refunds}
      </>,
    ],
    [t("faq.delete.q"), t("faq.delete.a", { settings: tn("settings"), action: ts("deleteTitle") })],
    [t("faq.advice.q"), tf("notAdvice")],
  );

  return (
    <section aria-labelledby="pricing-faq" className="mt-16 max-w-[820px]">
      <h2 id="pricing-faq" className={H2}>
        {t("faq.title")}
      </h2>
      <div className="mt-6 border-t border-line" data-pricing-faq>
        {items.map(([q, a]) => (
          <details key={q} className="group border-b border-line">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-4 text-[16.5px] font-semibold text-text hover:text-signal [&::-webkit-details-marker]:hidden">
              {q}
              <ChevronDownIcon aria-hidden className="size-5 shrink-0 text-muted transition-transform group-open:rotate-180" />
            </summary>
            <div className="pb-5 text-[15.5px] leading-[1.6] text-text-soft">{a}</div>
          </details>
        ))}
      </div>
    </section>
  );
}
