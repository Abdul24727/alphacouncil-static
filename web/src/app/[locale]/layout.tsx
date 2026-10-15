import type { Metadata } from "next";
import { Archivo, IBM_Plex_Sans_Arabic, Martian_Mono } from "next/font/google";
import { notFound } from "next/navigation";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { Providers } from "@/components/Providers";
import { LAYOUT_BOOT_SCRIPT } from "@/lib/layout-store";
import { dirFor, routing } from "@/i18n/routing";
import "../globals.css";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin", "latin-ext"],
  axes: ["wdth"],
});

const martian = Martian_Mono({
  variable: "--font-martian",
  subsets: ["latin"],
  axes: ["wdth"],
});

// Open item in BRAND.md: Arabic face under test. Archivo has no Arabic letters,
// so Arabic glyphs fall through to this face instead of the browser default.
const plexArabic = IBM_Plex_Sans_Arabic({
  variable: "--font-plex-arabic",
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "AlphaCouncil",
  description: "Research terminal for Gulf markets",
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function RootLayout({ children, params }: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);

  return (
    <html
      lang={locale}
      dir={dirFor(locale)}
      data-sidebar="expanded"
      data-copilot="open"
      className={`${archivo.variable} ${martian.variable} ${plexArabic.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: LAYOUT_BOOT_SCRIPT }} />
      </head>
      <body className="antialiased">
        <NextIntlClientProvider>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
