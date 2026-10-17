"use client";

import { useTranslations } from "next-intl";
import { Fragment, useState } from "react";
import { revealPanel } from "@/lib/panel-registry";
import type { Sources } from "./types";

const TOKEN = /(\[(?:P\d+|DB)\]|\*\*[^*]+\*\*|`[^`]+`)/g;

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
        if (/^`[^`]+`$/.test(piece)) return <code key={i} className="num text-[0.92em] text-text-soft">{piece.slice(1, -1)}</code>;
        return <Fragment key={i}>{piece}</Fragment>;
      })}
    </>
  );
}

/**
 * Just enough Markdown for chat answers: paragraphs, "-" lists, **bold**, `code`, "|" tables,
 * and citation tags as chips. Models are asked for show_table instead of "|" tables and for no
 * HTML; when they write them anyway, the table is drawn and stray tags ("<divider>") are dropped.
 */
export function RichText({ text, sources }: { text: string; sources: Sources }) {
  const blocks = text
    .replace(/\r/g, "")
    .replace(/<\/?[a-z][a-z0-9-]*\s*\/?>/gi, "")
    .split(/\n{2,}/);
  return (
    <div className="flex flex-col gap-2 leading-relaxed" dir="auto">
      {blocks.flatMap((block, i) => runs(block).map((run, k) => <Run key={`${i}.${k}`} run={run} sources={sources} />))}
    </div>
  );
}

type RunData = { table: boolean; lines: string[] };

/** A block's lines, grouped into "|" table rows and everything else. */
function runs(block: string): RunData[] {
  const out: RunData[] = [];
  for (const line of block.split("\n").filter((l) => l.trim())) {
    const table = /^\s*\|.*\|/.test(line);
    const last = out[out.length - 1];
    if (last && last.table === table) last.lines.push(line);
    else out.push({ table, lines: [line] });
  }
  return out;
}

function Run({ run, sources }: { run: RunData; sources: Sources }) {
  const { lines } = run;
  if (run.table) return <MarkdownTable lines={lines} sources={sources} />;
  if (lines.every((l) => /^\s*[-•*]\s+/.test(l))) {
    return (
      <ul className="flex list-disc flex-col gap-1 ps-4 marker:text-muted">
        {lines.map((l, j) => (
          <li key={j}>
            <Inline text={l.replace(/^\s*[-•*]\s+/, "")} sources={sources} />
          </li>
        ))}
      </ul>
    );
  }
  return (
    <p>
      {lines.map((l, j) => (
        <Fragment key={j}>
          {j > 0 && <br />}
          <Inline text={l.replace(/^#+\s*/, "")} sources={sources} />
        </Fragment>
      ))}
    </p>
  );
}

function MarkdownTable({ lines, sources }: { lines: string[]; sources: Sources }) {
  // "| a | b | [DB]": cells between the pipes; anything after the last pipe joins the last cell.
  const cells = (line: string) => {
    const parts = line.trim().replace(/^\|/, "").split("|");
    const tail = parts.length > 1 ? parts.pop()!.trim() : "";
    const row = parts.map((c) => c.trim());
    if (tail) row[row.length - 1] = `${row[row.length - 1]} ${tail}`;
    return row;
  };
  const rows = lines.map(cells).filter((r) => !r.every((c) => /^:?-{2,}:?$/.test(c)));
  const [head, ...body] = rows;
  const isNum = (c: string) => /^[-−+]?[\d.,]+%?x?(\s*\[(P\d+|DB)\])*$/.test(c);
  return (
    <div className="overflow-x-auto rounded-panel border border-line">
      <table className="w-full text-[12.5px]">
        <thead>
          <tr className="label-caps text-muted">
            {head?.map((c, j) => (
              <th key={j} className="px-2 py-1 text-start font-normal">
                <Inline text={c} sources={sources} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((r, i) => (
            <tr key={i} className="border-t border-line">
              {r.map((c, j) => (
                <td key={j} className={`px-2 py-1 ${isNum(c) ? "num text-end" : "text-text"}`}>
                  <Inline text={c} sources={sources} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
