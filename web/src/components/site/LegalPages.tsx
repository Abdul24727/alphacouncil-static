import { getTranslations } from "next-intl/server";
import { LEGAL_DOCS, type LegalDoc, legalDocument, merchantInfo } from "@/content/legal";
import { Link } from "@/i18n/navigation";
import { PAGE_LEAD, PAGE_TITLE } from "./PricingPage";
import { Arrow, WRAP } from "./ui";

type Props = { locale: string };

/** /legal — the current documents with their versions. */
export async function LegalIndex({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.legal" });
  return (
    <div className={`${WRAP} pt-10 md:pt-16`}>
      <h1 className={PAGE_TITLE}>{t("title")}</h1>
      <p className={PAGE_LEAD}>{t("lead")}</p>
      <ul className="mt-10 border-t border-line">
        {LEGAL_DOCS.map((doc) => {
          const d = legalDocument(locale, doc);
          return (
            <li key={doc} className="border-b border-line">
              <Link
                href={`/legal/${doc}`}
                className="group grid gap-x-6 gap-y-1 py-5 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-center"
              >
                <span className="text-[22px] font-bold group-hover:text-signal">{d.title}</span>
                <span className="text-[13px] text-muted">
                  {t("version")} <span className="num">{d.version}</span> · {t("effective")} <span className="num">{d.effective}</span>
                </span>
                <span className="text-signal">
                  <Arrow />
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
      <Merchant locale={locale} />
    </div>
  );
}

/** /legal/[doc] — the signed-off text, verbatim (src/content/legal, scripts/import-legal.py). */
export async function LegalDocPage({ locale, doc }: Props & { doc: LegalDoc }) {
  const t = await getTranslations({ locale, namespace: "site.legal" });
  const d = legalDocument(locale, doc);
  return (
    <div className={`${WRAP} pt-10 md:pt-16`}>
      <div className="mx-auto max-w-[820px]">
        <p className="mb-6 flex flex-wrap gap-x-4 gap-y-1 text-[13px] text-muted">
          <Link href="/legal" className="hover:text-text">
            {t("title")}
          </Link>
          <span aria-hidden>·</span>
          <Link href={`/legal/${doc}`} locale={locale === "ar" ? "en" : "ar"} lang={locale === "ar" ? "en" : "ar"} className="hover:text-text">
            {t("otherLanguage")}
          </Link>
        </p>
        <h1 className={PAGE_TITLE}>{d.title}</h1>
        <p className="mt-5 flex flex-wrap gap-x-5 gap-y-1 text-[13px] text-muted">
          <span>
            {t("version")} <span className="num text-text">{d.version}</span>
          </span>
          <span>
            {t("effective")} <span className="num text-text">{d.effective}</span>
          </span>
          {d.updated && (
            <span>
              {t("updated")} <span className="num text-text">{d.updated}</span>
            </span>
          )}
        </p>
        <p className="mt-3 text-[13px] text-muted">{d.operator}</p>
        {d.translationNote && (
          <p
            className="legal-note mt-3 text-[13px] text-muted [&_a]:text-signal"
            dangerouslySetInnerHTML={{ __html: d.translationNote }}
          />
        )}
        {d.toc.length > 0 && (
          <nav aria-label={t("onThisPage")} className="mt-8 border-y border-line py-5">
            <ol className="columns-1 gap-8 text-[14px] sm:columns-2">
              {d.toc.map((item) => (
                <li key={item.href} className="mb-1.5 break-inside-avoid">
                  <a href={item.href} className="text-text-soft hover:text-signal">
                    {item.label}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
        )}
        <div
          id="legal-body"
          data-canonical-hash={d.canonicalHash ?? undefined}
          className="legal mt-8 text-[15.5px] leading-[1.65]"
          dangerouslySetInnerHTML={{ __html: d.html }}
        />
        <Merchant locale={locale} />
      </div>
    </div>
  );
}

async function Merchant({ locale }: Props) {
  const t = await getTranslations({ locale, namespace: "site.legal" });
  return (
    // Verbatim registration details: the short address and e-mail stay in Latin letters.
    <section aria-label={t("merchant")} className="legal mt-12 border-t border-line pt-6 text-[13px]" id="merchant" data-latin-ok>
      {merchantInfo(locale).map((html) => (
        <p key={html} dangerouslySetInnerHTML={{ __html: html }} />
      ))}
    </section>
  );
}
