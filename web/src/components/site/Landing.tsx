import Image from "next/image";
import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import appDesktopAr from "@/assets/screens/app-desktop.ar.jpg";
import appDesktopEn from "@/assets/screens/app-desktop.en.jpg";
import appPhoneAr from "@/assets/screens/app-phone.ar.jpg";
import appPhoneEn from "@/assets/screens/app-phone.en.jpg";
import { Link } from "@/i18n/navigation";
import { getExchanges, getPlans } from "@/lib/api/server";
import { TEMPLATES, templateHref } from "@/lib/templates";
import { Arrow, ButtonLink, Db, SECTION_TITLE, Unavailable, WRAP } from "./ui";

type Props = { locale: string };

const db = (c: React.ReactNode) => <Db>{c}</Db>;

/** "/" — BRAND.md landing: condensed hero, the real app as hero image, three split columns,
 * templates list, the exchanges table and a final call to action. */
export async function Landing({ locale }: Props) {
  return (
    <>
      <Hero locale={locale} />
      <Shot locale={locale} />
      <How locale={locale} />
      <Templates locale={locale} />
      <Markets locale={locale} />
      <Cta locale={locale} />
    </>
  );
}

async function Hero({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.hero" });
  return (
    <section className={`${WRAP} grid grid-cols-[repeat(auto-fit,minmax(min(340px,100%),1fr))] items-end gap-10 pt-10 pb-10 md:pt-[72px]`}>
      <h1 className="text-[clamp(48px,7vw,104px)] font-extrabold uppercase leading-[0.92] tracking-[-0.01em] [font-stretch:80%] rtl:leading-[1.25]">
        {t.rich("title", { em: (c) => <span className="text-signal">{c}</span> })}
      </h1>
      <div className="flex max-w-[460px] flex-col gap-6">
        <p className="text-[18px] leading-[1.55] text-text-soft">{t("lead")}</p>
        <div className="flex flex-wrap gap-3">
          <ButtonLink href="/signup">{t("start")}</ButtonLink>
          <ButtonLink href={{ pathname: "/", hash: "how" }} variant="outline">
            {t("how")}
          </ButtonLink>
        </div>
        <Suspense fallback={<p className="label-caps h-4 text-[11.5px] text-muted" />}>
          <Coverage locale={locale} />
        </Suspense>
      </div>
    </section>
  );
}

async function Coverage({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site" });
  const exchanges = await getExchanges();
  if (!exchanges) return <Unavailable>{t("unavailable")}</Unavailable>;
  const equities = exchanges.reduce((n, e) => n + e.equities, 0);
  return (
    <p className="label-caps text-[11.5px] text-muted" data-coverage>
      {t.rich("hero.coverage", { n: db, exchanges: String(exchanges.length), equities: String(equities) })}
    </p>
  );
}

async function Shot({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.hero" });
  const ar = locale === "ar";
  return (
    <section aria-label={t("shotAlt")} className={WRAP}>
      <div className="hidden overflow-hidden rounded-panel border border-line sm:block">
        <Image
          src={ar ? appDesktopAr : appDesktopEn}
          alt={t("shotAlt")}
          sizes="(min-width: 1320px) 1256px, calc(100vw - 64px)"
          preload
          className="h-auto w-full"
        />
      </div>
      <div className="mx-auto max-w-[390px] overflow-hidden rounded-panel border border-line sm:hidden">
        <Image src={ar ? appPhoneAr : appPhoneEn} alt={t("shotAlt")} sizes="calc(100vw - 32px)" className="h-auto w-full" />
      </div>
      <p className="mt-2.5 font-mono text-[11px] text-muted">{t("shotCaption")}</p>
    </section>
  );
}

async function How({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.how" });
  const columns = ["groups", "receipts", "age"] as const;
  return (
    <section id="how" className={`${WRAP} scroll-mt-6 pt-24 pb-10 md:pt-[120px]`}>
      <h2 className={`${SECTION_TITLE} mb-12 max-w-[820px]`}>{t("title")}</h2>
      <div className="grid border-t border-line md:grid-cols-3">
        {columns.map((key, i) => (
          <div
            key={key}
            className={`flex flex-col gap-3 py-7 md:px-7 md:first:ps-0 ${i > 0 ? "border-t border-line md:border-t-0 md:border-s" : ""}`}
          >
            <h3 className="text-[24px] font-bold leading-tight">{t(`${key}.title`)}</h3>
            <p className="text-[17px] font-medium leading-snug text-text">{t(`${key}.lead`)}</p>
            <p className="text-[15.5px] leading-[1.6] text-text-soft">{t(`${key}.body`)}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

async function Templates({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.templates" });
  const tt = await getTranslations({ locale, namespace: "templates" });
  return (
    <section id="templates" className={`${WRAP} scroll-mt-6 pt-24 pb-10 md:pt-[100px]`}>
      <div className="mb-9 flex flex-wrap items-end justify-between gap-5">
        <h2 className={SECTION_TITLE}>{t("title")}</h2>
        <p className="max-w-[420px] text-[15.5px] leading-[1.6] text-text-soft">{t("lead")}</p>
      </div>
      <ul className="border-t border-line">
        {TEMPLATES.map((name) => (
          <li key={name} className="border-b border-line">
            <Link
              href={templateHref(name)}
              className="group grid gap-x-6 gap-y-2 py-6 md:grid-cols-[minmax(180px,1fr)_minmax(0,2fr)_auto] md:items-center"
            >
              <span className="text-[26px] font-bold leading-tight [font-stretch:95%] group-hover:text-signal">
                {tt(`names.${name}`)}
              </span>
              <span className="text-[15px] leading-normal text-text-soft">{tt(`descriptions.${name}`)}</span>
              <span className="label-caps flex items-center gap-1.5 text-[12px] text-signal">
                {t("open")} <Arrow />
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

async function Markets({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.markets" });
  return (
    <section id="markets" className={`${WRAP} grid scroll-mt-6 gap-12 pt-24 pb-10 md:grid-cols-2 md:pt-[100px]`}>
      <div className="flex flex-col gap-4">
        <h2 className={SECTION_TITLE}>{t("title")}</h2>
        <p className="max-w-[420px] text-[15.5px] leading-[1.6] text-text-soft">{t("lead")}</p>
      </div>
      <Suspense fallback={<ExchangeRows rows={null} locale={locale} />}>
        <ExchangeTable locale={locale} />
      </Suspense>
    </section>
  );
}

async function ExchangeTable({ locale }: Props) {
  const rows = await getExchanges();
  return <ExchangeRows rows={rows ?? []} locale={locale} />;
}

/** rows: null while loading (skeleton, no numbers), [] when the API could not answer. */
async function ExchangeRows({ rows, locale }: { rows: { exchange: string; equities: number }[] | null; locale: string }) {
  const t = await getTranslations({ locale, namespace: "site" });
  const tx = await getTranslations({ locale, namespace: "exchanges" });
  return (
    <table className="w-full text-[15px]" data-exchanges>
      <thead>
        <tr className="label-caps text-muted">
          <th className="pb-3 text-start font-normal">{t("markets.market")}</th>
          <th className="pb-3 text-start font-normal">{t("markets.exchange")}</th>
          <th className="pb-3 text-end font-normal">{t("markets.equities")}</th>
        </tr>
      </thead>
      <tbody>
        {rows === null ? (
          Array.from({ length: 7 }, (_, i) => (
            <tr key={i} className="border-t border-line">
              <td colSpan={3} className="h-[49px]" />
            </tr>
          ))
        ) : rows.length === 0 ? (
          <tr className="border-t border-line">
            <td colSpan={3} className="py-3.5">
              <Unavailable>{t("unavailable")}</Unavailable>
            </td>
          </tr>
        ) : (
          rows.map((e) => (
            <tr key={e.exchange} className="border-t border-line">
              <td className="py-3.5">{t(`markets.countries.${e.exchange}` as "markets.countries.TADAWUL")}</td>
              <td className="py-3.5 text-text-soft">{tx(e.exchange as "TADAWUL")}</td>
              <td className="py-3.5 text-end text-[13px] text-text-soft">
                <Db>{e.equities}</Db>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}

async function Cta({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.cta" });
  return (
    <section className={`${WRAP} flex flex-wrap items-center justify-between gap-8 pt-24 pb-4 md:pt-[100px]`}>
      <h2 className="text-[clamp(40px,6vw,84px)] font-extrabold uppercase leading-[0.95] [font-stretch:80%] rtl:leading-[1.25]">
        {t("title")}
      </h2>
      <div className="flex flex-col items-start gap-3">
        <ButtonLink href="/signup" size="lg">
          {t("start")}
        </ButtonLink>
        <Suspense fallback={<p className="label-caps h-4 text-[11.5px] text-muted" />}>
          <PlansLine locale={locale} />
        </Suspense>
      </div>
    </section>
  );
}

async function PlansLine({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site" });
  const plans = await getPlans();
  const pro = plans?.plans.find((p) => p.id === "pro");
  if (!plans || !pro) return <Unavailable>{t("unavailable")}</Unavailable>;
  return (
    <Link href="/pricing" className="label-caps text-[11.5px] text-muted hover:text-text" data-plans>
      {t.rich("cta.plans", {
        n: db,
        price: String(pro.price_sar),
        currency: t.has(`currency.${pro.currency}` as "currency.SAR") ? t(`currency.${pro.currency}` as "currency.SAR") : pro.currency,
      })}
    </Link>
  );
}
