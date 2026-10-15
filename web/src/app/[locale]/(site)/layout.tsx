import { setRequestLocale } from "next-intl/server";
import { SiteFooter } from "@/components/site/SiteFooter";
import { SiteHeader } from "@/components/site/SiteHeader";
import type { Locale } from "@/i18n/routing";

/** Public pages (/, /pricing, /methodology, /legal): site header and footer, no app shell. */
export default async function SiteLayout({ children, params }: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);
  return (
    <div className="flex min-h-dvh flex-col text-[15.5px] leading-normal">
      <SiteHeader />
      <main id="content" className="flex-1">
        {children}
      </main>
      <SiteFooter />
    </div>
  );
}
