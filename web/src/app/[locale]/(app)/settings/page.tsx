import { PlaceholderPage } from "@/components/PlaceholderPage";

export default async function Page({ params }: PageProps<"/[locale]/settings">) {
  const { locale } = await params;
  return <PlaceholderPage locale={locale} page="settings" phase={5} />;
}
