import { getTranslations, setRequestLocale } from "next-intl/server";
import { PhasePlaceholder } from "@/components/PhasePlaceholder";
import { WorkHeader } from "@/components/shell/WorkHeader";
import type { Locale } from "@/i18n/routing";

type PageKey = "home" | "portfolio" | "screener" | "markets" | "templates" | "dashboards" | "settings" | "stock";

/** A signed-in page whose content a later phase builds. */
export async function PlaceholderPage({
  locale,
  page,
  phase,
  title,
  subtitle,
}: {
  locale: string;
  page: PageKey;
  phase: number;
  title?: string;
  subtitle?: React.ReactNode;
}) {
  setRequestLocale(locale as Locale);
  const tp = await getTranslations("pages");
  const t = await getTranslations("placeholder");

  return (
    <>
      <WorkHeader title={title ?? tp(page)}>{subtitle}</WorkHeader>
      <div className="grid flex-1 auto-rows-min grid-cols-12 gap-2.5 overflow-y-auto p-2.5">
        <div className="col-span-12">
          <PhasePlaceholder phase={phase} what={t(page)} />
        </div>
      </div>
    </>
  );
}
