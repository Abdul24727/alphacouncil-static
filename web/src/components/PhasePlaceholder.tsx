import { useTranslations } from "next-intl";

/**
 * Honest stand-in for a panel that a later phase builds. Shows no numbers:
 * BRAND.md allows only database values or a labelled placeholder.
 */
export function PhasePlaceholder({ phase, what }: { phase: number; what: string }) {
  const t = useTranslations("placeholder");
  return (
    <section className="flex min-h-40 flex-col rounded-panel border border-line bg-panel">
      <header className="flex h-9 items-center gap-2 border-b border-line px-3">
        <span aria-hidden className="size-1.5 rounded-full bg-neutral-seat" />
        <span className="label-caps text-muted">{t("phase", { phase })}</span>
      </header>
      <p className="p-3 text-text-soft">{what}</p>
    </section>
  );
}
