import { redirect } from "@/i18n/navigation";

// The public landing page is rebuilt in Phase 6; until then / opens the app.
export default async function Page({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  redirect({ href: "/home", locale });
}
