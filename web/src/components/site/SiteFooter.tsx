import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { LEGAL_DOCS } from "@/content/legal";
import { Logo } from "./SiteHeader";
import { WRAP } from "./ui";

export async function SiteFooter() {
  const t = await getTranslations("site");
  const product = [
    ["/methodology", t("nav.methodology")],
    ["/pricing", t("nav.pricing")],
    ["/markets", t("nav.markets")],
    ["/templates", t("nav.templates")],
  ] as const;

  return (
    <footer className="mt-24 border-t border-line">
      <div className={`${WRAP} flex flex-col gap-8 py-10 text-[13px] text-muted md:flex-row md:justify-between`}>
        <div className="flex max-w-sm flex-col gap-3">
          <Logo size="sm" />
          <p>{t("footer.notAdvice")}</p>
          <p>{t("footer.entity")}</p>
        </div>
        <div className="flex flex-col gap-4 sm:flex-row sm:gap-16">
          <nav aria-label={t("footer.product")} className="flex flex-col gap-2">
            {product.map(([href, label]) => (
              <Link key={href} href={href} className="hover:text-text">
                {label}
              </Link>
            ))}
          </nav>
          <nav aria-label={t("footer.legal")} className="flex flex-col gap-2">
            {LEGAL_DOCS.map((doc) => (
              <Link key={doc} href={`/legal/${doc}`} className="hover:text-text">
                {t(`legal.short.${doc}`)}
              </Link>
            ))}
            <Link href={{ pathname: "/legal", hash: "merchant" }} className="hover:text-text">
              {t("legal.merchant")}
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
