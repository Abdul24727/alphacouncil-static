import { PlaceholderPage } from "@/components/PlaceholderPage";

export default async function Page({ params }: PageProps<"/[locale]/templates">) {
  const { locale } = await params;
  return <PlaceholderPage locale={locale} page="templates" phase={5} />;
}
