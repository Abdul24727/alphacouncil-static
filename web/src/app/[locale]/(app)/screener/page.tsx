import { PlaceholderPage } from "@/components/PlaceholderPage";

export default async function Page({ params }: PageProps<"/[locale]/screener">) {
  const { locale } = await params;
  return <PlaceholderPage locale={locale} page="screener" phase={5} />;
}
