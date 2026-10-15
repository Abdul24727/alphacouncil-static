import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import { LegalDocPage } from "@/components/site/LegalPages";
import { isLegalDoc, LEGAL_DOCS, legalDocument } from "@/content/legal";
import type { Locale } from "@/i18n/routing";

export function generateStaticParams() {
  return LEGAL_DOCS.map((doc) => ({ doc }));
}

export async function generateMetadata({ params }: PageProps<"/[locale]/legal/[doc]">): Promise<Metadata> {
  const { locale, doc } = await params;
  if (!isLegalDoc(doc)) return {};
  return { title: `${legalDocument(locale, doc).title} · AlphaCouncil` };
}

export default function Page({ params }: PageProps<"/[locale]/legal/[doc]">) {
  // `doc` is URL data: it renders behind Suspense (still prerendered for every document).
  return (
    <Suspense fallback={<div className="min-h-[60vh]" />}>
      <Doc params={params} />
    </Suspense>
  );
}

async function Doc({ params }: Pick<PageProps<"/[locale]/legal/[doc]">, "params">) {
  const { locale, doc } = await params;
  setRequestLocale(locale as Locale);
  if (!isLegalDoc(doc)) notFound();
  return <LegalDocPage locale={locale} doc={doc} />;
}
