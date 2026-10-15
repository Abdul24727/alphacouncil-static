import { PlaceholderPage } from "@/components/PlaceholderPage";

export default async function Page({ params }: PageProps<"/[locale]/dashboards">) {
  const { locale } = await params;
  return <PlaceholderPage locale={locale} page="dashboards" phase={5} />;
}
