import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { TemplatesList } from "@/components/templates/TemplateViews";
import { WorkHeader } from "@/components/shell/WorkHeader";
import type { Locale } from "@/i18n/routing";
import { localizedMetadata, titled } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/templates">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "pages" });
  const m = await getTranslations({ locale, namespace: "meta" });
  return localizedMetadata(locale, "/templates", titled(t("templates")), m("templates"));
}

export default async function Page({ params }: PageProps<"/[locale]/templates">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  const t = await getTranslations("pages");
  return (
    <>
      <WorkHeader title={t("templates")} />
      <TemplatesList />
    </>
  );
}
