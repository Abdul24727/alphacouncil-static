import { PlaceholderPage } from "@/components/PlaceholderPage";

export default async function Page({ params }: PageProps<"/[locale]/portfolio">) {
  const { locale } = await params;
  return <PlaceholderPage locale={locale} page="portfolio" phase={5} />;
}
