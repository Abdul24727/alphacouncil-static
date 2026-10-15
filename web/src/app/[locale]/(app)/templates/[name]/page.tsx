import { Suspense } from "react";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { WorkHeader } from "@/components/shell/WorkHeader";

export default function Page({ params }: PageProps<"/[locale]/templates/[name]">) {
  return (
    <Suspense fallback={<WorkHeader title="" />}>
      <TemplatePage params={params} />
    </Suspense>
  );
}

async function TemplatePage({ params }: Pick<PageProps<"/[locale]/templates/[name]">, "params">) {
  const { locale, name } = await params;
  return (
    <PlaceholderPage
      locale={locale}
      page="templates"
      phase={5}
      subtitle={<span className="label-caps text-muted">{decodeURIComponent(name)}</span>}
    />
  );
}
