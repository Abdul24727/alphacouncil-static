import { PlaceholderPage } from "@/components/PlaceholderPage";

export default async function Page({ params }: PageProps<"/[locale]/markets">) {
  const { locale } = await params;
  return <PlaceholderPage locale={locale} page="markets" phase={6} />;
}
