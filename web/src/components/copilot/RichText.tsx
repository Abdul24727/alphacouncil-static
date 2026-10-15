"use client";

import { useTranslations } from "next-intl";
import { Fragment, useState } from "react";
import { revealPanel } from "@/lib/panel-registry";
import type { Sources } from "./types";

const TOKEN = /(\[(?:P\d+|DB)\]|\*\*[^*]+\*\*)/g;

/** A citation tag rendered as a chip; panel chips scroll to and flash that panel. */
export function CitationChip({ tag, sources }: { tag: string; sources: Sources }) {
  const t = useTranslations("copilot");
  const [missing, setMissing] = useState(false);
  const src = sources[tag];
  if (tag === "DB" || !src?.id) {
    return (
      <span className="label-caps mx-0.5 inline-flex items-center rounded-chip border border-line px-1 align-[1px] text-muted" title={t("database")}>
        DB
      </span>
    );
  }
  return (
    <button
      type="button"
      data-citation={src.id}
      title={missing ? t("notOnPage") : src.title}
      onClick={() => setMissing(!revealPanel(src.id!))}
      className={`label-caps mx-0.5 inline-flex max-w-40 items-center gap-1 rounded-chip border px-1 align-[1px] ${
        missing ? "border-line text-muted line-through" : "border-signal/50 text-signal hover:bg-signal/10"
      }`}
    >
      <span>{tag}</span>
      <span className="truncate normal-case tracking-normal">{src.title}</span>
    </button>
  );
}

function Inline({ text, sources }: { text: string; sources: Sources }) {
  return (
    <>
      {text.split(TOKEN).map((piece, i) => {
        if (/^\[(P\d+|DB)\]$/.test(piece)) return <CitationChip key={i} tag={piece.slice(1, -1)} sources={sources} />;
        if (/^\*\*[^*]+\*\*$/.test(piece)) return <strong key={i} className="font-semibold text-text">{piece.slice(2, -2)}</strong>;
        return <Fragment key={i}>{piece}</Fragment>;
      })}
    </>
  );
}

/**
 * Just enough Markdown for chat answers: paragraphs, "-" lists, **bold**, and
 * citation tags as chips. Tables come through show_table, not Markdown.
 */
export function RichText({ text, sources }: { text: string; sources: Sources }) {
  const blocks = text.replace(/\r/g, "").split(/\n{2,}/);
  return (
    <div className="flex flex-col gap-2 leading-relaxed" dir="auto">
      {blocks.map((block, i) => {
        const lines = block.split("\n").filter((l) => l.trim());
        if (lines.length && lines.every((l) => /^\s*[-•*]\s+/.test(l))) {
          return (
            <ul key={i} className="flex list-disc flex-col gap-1 ps-4 marker:text-muted">
              {lines.map((l, j) => (
                <li key={j}>
                  <Inline text={l.replace(/^\s*[-•*]\s+/, "")} sources={sources} />
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={i}>
            {lines.map((l, j) => (
              <Fragment key={j}>
                {j > 0 && <br />}
                <Inline text={l.replace(/^#+\s*/, "")} sources={sources} />
              </Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}
