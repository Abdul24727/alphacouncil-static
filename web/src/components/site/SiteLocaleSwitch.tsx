"use client";

import { useLocale, useTranslations } from "next-intl";
import { WithPathname } from "@/components/shell/WithPathname";
import { Link } from "@/i18n/navigation";

/** The same page in the other language: "ع" on English pages, "EN" on Arabic ones. */
export function SiteLocaleSwitch() {
  const t = useTranslations("site.nav");
  const locale = useLocale();
  const other = locale === "ar" ? "en" : "ar";
  return (
    <WithPathname
      render={(pathname) => (
        <Link
          href={pathname ?? "/"}
          locale={other}
          aria-label={t("language")}
          className={`text-muted hover:text-text ${other === "en" ? "label-caps" : "text-[16px] leading-none"}`}
        >
          {other === "en" ? "EN" : "ع"}
        </Link>
      )}
    />
  );
}
