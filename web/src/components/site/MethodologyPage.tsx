import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { Link } from "@/i18n/navigation";
import { getMethodology, type Methodology } from "@/lib/api/server";
import { ruleArgs } from "@/lib/council-rules";
import { H2, PAGE_LEAD, PAGE_TITLE } from "./PricingPage";
import { Db, Unavailable, WRAP } from "./ui";

type Props = { locale: string };

const TH = "label-caps pb-2 pe-4 text-start font-normal text-muted";
const TD = "border-t border-line py-2.5 pe-4 align-top";

/** /methodology — the council's rules, data sources and freshness rules, read from the API. */
export async function MethodologyPage({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.methodology" });
  return (
    <div className={`${WRAP} pt-10 md:pt-16`}>
      <h1 className={PAGE_TITLE}>{t("title")}</h1>
      <p className={PAGE_LEAD}>{t("lead")}</p>
      <Suspense fallback={<div className="h-[60vh]" />}>
        <Loaded locale={locale} />
      </Suspense>
    </div>
  );
}

async function Loaded({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site" });
  const m = await getMethodology();
  if (!m) {
    return (
      <p className="mt-12">
        <Unavailable>{t("unavailable")}</Unavailable>
      </p>
    );
  }
  return (
    <>
      <Council m={m} locale={locale} />
      <Data m={m} locale={locale} />
      <Fresh m={m} locale={locale} />
      <Limits locale={locale} />
    </>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="mt-16 flex scroll-mt-6 flex-col gap-4 border-t border-line pt-10">
      <h2 className={H2}>{title}</h2>
      {children}
    </section>
  );
}

const Body = ({ children }: { children: React.ReactNode }) => (
  <p className="max-w-[760px] text-[15.5px] leading-[1.65] text-text-soft">{children}</p>
);

async function Council({ m, locale }: { m: Methodology; locale: string }) {
  const t = await getTranslations({ locale, namespace: "site.methodology.council" });
  const ts = await getTranslations({ locale, namespace: "stock.council" });
  return (
    <Section id="council" title={t("title")}>
      <Body>{t("body")}</Body>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-[15px]" data-seats>
          <thead>
            <tr>
              <th className={TH}>{t("seat")}</th>
              <th className={TH}>{t("reads")}</th>
              <th className={TH}>{t("rule")}</th>
            </tr>
          </thead>
          <tbody>
            {m.seats.map((s) => (
              <tr key={s.seat}>
                <td className={`${TD} headline text-[18px]`}>{ts(`seats.${s.seat}` as "seats.value")}</td>
                <td className={`${TD} text-text-soft`}>
                  {s.inputs.map((i) => ts(`inputs.${i}` as "inputs.pe")).join(" · ")}
                </td>
                {/* The thresholds in the rule come from the API (council.THRESHOLDS). */}
                <td className={`${TD} text-text-soft`} data-db>
                  {ts(`rules.${s.seat}` as "rules.value", ruleArgs(s.thresholds))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}

function weekdayNames(days: number[], locale: string) {
  // Monday = 0, as Python's weekday(); 2024-01-01 was a Monday.
  const fmt = new Intl.DateTimeFormat(locale === "ar" ? "ar" : "en", { weekday: "long", timeZone: "UTC" });
  return days.map((d) => fmt.format(new Date(Date.UTC(2024, 0, 1 + d)))).join(locale === "ar" ? "، " : ", ");
}

async function Data({ m, locale }: { m: Methodology; locale: string }) {
  const t = await getTranslations({ locale, namespace: "site.methodology.data" });
  const tm = await getTranslations({ locale, namespace: "site.markets.countries" });
  const tx = await getTranslations({ locale, namespace: "exchanges" });
  const db = (c: React.ReactNode) => <Db>{c}</Db>;
  return (
    <Section id="data" title={t("title")}>
      <Body>{t("body")}</Body>
      <Body>{t.rich("run", { n: db, time: m.pipeline_run_utc })}</Body>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-[15px]" data-coverage-table>
          <thead>
            <tr>
              <th className={TH}>{t("market")}</th>
              <th className={TH}>{t("exchange")}</th>
              <th className={`${TH} text-end`}>{t("equities")}</th>
              <th className={`${TH} ps-6`}>{t("weekend")}</th>
            </tr>
          </thead>
          <tbody>
            {m.exchanges.map((e) => (
              <tr key={e.exchange}>
                <td className={TD}>{tm(e.exchange as "TADAWUL")}</td>
                <td className={`${TD} text-text-soft`}>{tx(e.exchange as "TADAWUL")}</td>
                <td className={`${TD} text-end text-text-soft`}>
                  <Db>{e.equities}</Db>
                </td>
                <td className={`${TD} ps-6 text-text-soft`}>{weekdayNames(e.weekend, locale)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Body>{t.rich("total", { n: db, equities: String(m.equities) })}</Body>
    </Section>
  );
}

async function Fresh({ m, locale }: { m: Methodology; locale: string }) {
  const t = await getTranslations({ locale, namespace: "site.methodology.fresh" });
  const db = (c: React.ReactNode) => <Db>{c}</Db>;
  return (
    <Section id="freshness" title={t("title")}>
      <Body>{t("body")}</Body>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-[15px]" data-freshness-table>
          <thead>
            <tr>
              <th className={TH}>{t("dataset")}</th>
              <th className={`${TH} text-end`}>{t("maxAge")}</th>
              <th className={`${TH} ps-6`}>{t("counted")}</th>
              <th className={`${TH} text-end`}>{t("tracked")}</th>
            </tr>
          </thead>
          <tbody>
            {m.freshness.map((f) => (
              <tr key={`${f.category}-${f.max_age_days}`}>
                <td className={TD}>
                  {t.has(`categories.${f.category}` as "categories.prices")
                    ? t(`categories.${f.category}` as "categories.prices")
                    : f.category}
                </td>
                <td className={`${TD} text-end text-text-soft`}>
                  {f.max_age_days == null ? "—" : <Db>{f.max_age_days}</Db>}
                </td>
                <td className={`${TD} ps-6 text-text-soft`}>{f.trading_days ? t("tradingDays") : t("calendarDays")}</td>
                <td className={`${TD} text-end text-text-soft`}>
                  <Db>{f.tickers}</Db>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Body>{t.rich("fallback", { n: db, days: String(m.price_max_age_days) })}</Body>
    </Section>
  );
}

async function Limits({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.methodology.limits" });
  return (
    <Section id="limits" title={t("title")}>
      <Body>
        {t.rich("body", {
          link: (c) => (
            <Link href="/legal/ai-financial-disclaimer" className="text-signal hover:underline">
              {c}
            </Link>
          ),
        })}
      </Body>
    </Section>
  );
}
