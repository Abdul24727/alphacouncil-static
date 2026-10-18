"use client";

import Image from "next/image";
import { useLocale, useTranslations } from "next-intl";
import { Fragment } from "react";
import { splitText, type Flags, type SeatInfo, type Source } from "@/lib/debate";

export const seatName = (s: SeatInfo | undefined, locale: string) => (s ? (locale === "ar" ? s.name_ar : s.name_en) : "");
/** Surname for tags and "X answers Y": the last word of the name in the page's language. */
export const seatShort = (s: SeatInfo | undefined, locale: string) => seatName(s, locale).split(" ").slice(-1)[0] ?? "";
export const seatLens = (s: SeatInfo | undefined, locale: string) => (s ? (locale === "ar" ? s.lens_ar : s.lens_en) : "");

export function useSeats(seats: SeatInfo[] | undefined) {
  const locale = useLocale();
  const byId = new Map((seats ?? []).map((s) => [s.id, s]));
  return {
    seat: (id: string | null | undefined) => (id ? byId.get(id) : undefined),
    name: (id: string | null | undefined) => seatName(id ? byId.get(id) : undefined, locale),
    short: (id: string | null | undefined) => seatShort(id ? byId.get(id) : undefined, locale),
    lens: (id: string | null | undefined) => seatLens(id ? byId.get(id) : undefined, locale),
  };
}

/**
 * A seat's portrait slot: the owner's caricature when the seat file names one
 * (web/public/advisors), otherwise the seat's initials on a graphite disc.
 */
export function SeatDisc({ seat, size = 56, active = false }: { seat: SeatInfo | undefined; size?: number; active?: boolean }) {
  const ring = active ? "border-signal" : seat?.role === "chair" ? "border-muted/60 border-dashed" : "border-line";
  return (
    <span
      aria-hidden
      className={`relative flex shrink-0 items-center justify-center overflow-hidden rounded-full border bg-panel-raised ${ring}`}
      style={{ width: size, height: size }}
    >
      {seat?.portrait ? (
        <Image src={seat.portrait} alt="" width={size} height={size} className="size-full object-cover" />
      ) : (
        <span className="num text-text-soft" style={{ fontSize: Math.round(size * 0.3) }}>
          {seat?.initials ?? ""}
        </span>
      )}
    </span>
  );
}

/** "···" over a seat while it writes; the space stays reserved so the arc does not jump. */
export function WritingMark({ on }: { on: boolean }) {
  const t = useTranslations("debate");
  return (
    <span
      className={`num rounded-chip border px-1.5 text-[12px] leading-[16px] ${on ? "animate-pulse border-signal/60 text-signal" : "invisible border-transparent"}`}
      title={on ? t("writing") : undefined}
    >
      ···
    </span>
  );
}

/** A citation tag as a chip naming the dataset it points to. */
function Tag({ tag, sources }: { tag: string; sources: Record<string, Source> | null | undefined }) {
  const locale = useLocale();
  const src = sources?.[tag];
  const title = src ? (locale === "ar" ? src.title_ar : src.title_en) : tag;
  return (
    <span
      className="label-caps mx-0.5 inline-flex items-center rounded-chip border border-line px-1 align-[1px] text-muted"
      title={title}
      data-cite={tag}
    >
      {tag}
    </span>
  );
}

/** A seat's text: citation chips, and figures the checks could not find in the data marked as such. */
export function DebateText({
  text,
  flags,
  sources,
  className = "",
}: {
  text: string;
  flags?: Flags | null;
  sources: Record<string, Source> | null | undefined;
  className?: string;
}) {
  const t = useTranslations("debate");
  const paragraphs = text.split(/\n{2,}/).filter((p) => p.trim());
  return (
    <div className={`flex flex-col gap-1.5 leading-relaxed ${className}`} dir="auto">
      {paragraphs.map((p, i) => (
        <p key={i}>
          {splitText(p, flags?.unverified).map((piece, j) =>
            piece.kind === "tag" ? (
              <Tag key={j} tag={piece.text} sources={sources} />
            ) : piece.kind === "unverified" ? (
              <span key={j} className="text-stale underline decoration-dotted" title={t("unverified")} data-unverified>
                {piece.text}
              </span>
            ) : (
              <Fragment key={j}>{piece.text}</Fragment>
            ),
          )}
        </p>
      ))}
    </div>
  );
}

/** What the checks did to a turn, under it: figures not found in the data, advice removed. */
export function FlagNotes({ flags }: { flags: Flags | null | undefined }) {
  const t = useTranslations("debate");
  if (!flags || (!flags.unverified.length && !flags.removed)) return null;
  return (
    <div className="mt-1 flex flex-col gap-0.5 text-[11.5px] text-muted">
      {flags.unverified.length > 0 && <p>{t("unverifiedNote", { figures: flags.unverified.join(", ") })}</p>}
      {flags.removed > 0 && <p>{t("removedNote", { n: flags.removed })}</p>}
    </div>
  );
}

/** An option's letter in a small box, as on the round card and the options list. */
export function OptionId({ id, strong = false }: { id: string; strong?: boolean }) {
  return (
    <span
      className={`num flex size-5 shrink-0 items-center justify-center rounded-chip border text-[11px] ${
        strong ? "border-signal text-signal" : "border-line text-text-soft"
      }`}
    >
      {id}
    </span>
  );
}
