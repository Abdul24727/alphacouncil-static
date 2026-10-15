import { Suspense } from "react";
import { getTranslations, setRequestLocale } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import { WorkHeader } from "@/components/shell/WorkHeader";
import { TemplateView } from "@/components/templates/TemplateViews";

// The template name comes from the URL, so it streams in behind Suspense.
export default function Page({ params }: PageProps<"/[locale]/templates/[name]">) {
  return (
    <Suspense fallback={<WorkHeader title="" />}>
      <Template params={params} />
    </Suspense>
  );
}

async function Template({ params }: Pick<PageProps<"/[locale]/templates/[name]">, "params">) {
  const { locale, name } = await params;
  setRequestLocale(locale as Locale);
  const t = await getTranslations("templates");
  const key = decodeURIComponent(name);
  return (
    <>
      <WorkHeader title={t.has(`names.${key}`) ? t(`names.${key}`) : key} />
      <TemplateView name={key} />
    </>
  );
}
