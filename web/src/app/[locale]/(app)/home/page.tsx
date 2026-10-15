import { PlaceholderPage } from "@/components/PlaceholderPage";

export default async function Page({ params }: PageProps<"/[locale]/home">) {
  const { locale } = await params;
  return <PlaceholderPage locale={locale} page="home" phase={5} />;
}
