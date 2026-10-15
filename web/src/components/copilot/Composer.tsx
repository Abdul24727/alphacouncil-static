"use client";

import { PaperPlaneIcon, StopIcon } from "@radix-ui/react-icons";
import { useTranslations } from "next-intl";
import { useMemo, useRef, useState } from "react";
import { useCopilot } from "@/lib/copilot-store";
import { usePanelRegistry } from "@/lib/panel-registry";

const SKILLS = ["dividend", "peers", "news", "council"] as const;

type Menu =
  | { kind: "mention"; query: string; start: number }
  | { kind: "skill"; query: string }
  | null;

/** Detect "@query" before the caret or "/query" as the whole input. */
function menuAt(text: string, caret: number): Menu {
  const before = text.slice(0, caret);
  const at = /(^|\s)@([^\s@]*)$/.exec(before);
  if (at) return { kind: "mention", query: at[2], start: caret - at[2].length - 1 };
  const slash = /^\/(\S*)$/.exec(text);
  if (slash) return { kind: "skill", query: slash[1] };
  return null;
}

export function Composer({
  busy,
  onSend,
  onStop,
}: {
  busy: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
}) {
  const t = useTranslations("copilot");
  const panels = usePanelRegistry((s) => s.panels);
  const attach = useCopilot((s) => s.attach);
  const [text, setText] = useState("");
  const [menu, setMenu] = useState<Menu>(null);
  const [active, setActive] = useState(0);
  const ref = useRef<HTMLTextAreaElement>(null);

  const options = useMemo(() => {
    if (menu?.kind === "mention") {
      const q = menu.query.toLowerCase();
      return Object.values(panels)
        .filter((p) => !q || p.title.toLowerCase().includes(q) || p.id.toLowerCase().includes(q))
        .slice(0, 8)
        .map((p) => ({ key: p.id, label: p.title, hint: p.ticker ?? "" }));
    }
    if (menu?.kind === "skill") {
      return SKILLS.filter((k) => k.startsWith(menu.query.toLowerCase())).map((k) => ({
        key: k,
        label: t(`skills.${k}.label`),
        hint: t(`skills.${k}.prompt`),
      }));
    }
    return [];
  }, [menu, panels, t]);

  const update = (value: string, caret: number) => {
    setText(value);
    setMenu(menuAt(value, caret));
    setActive(0);
  };

  const choose = (i: number) => {
    const opt = options[i];
    if (!opt || !menu) return;
    if (menu.kind === "mention") {
      const p = panels[opt.key];
      attach({ id: p.id, title: p.title, ticker: p.ticker });
      const caret = ref.current?.selectionStart ?? text.length;
      setText(text.slice(0, menu.start) + text.slice(caret));
    } else {
      setText(t(`skills.${opt.key}.prompt`));
    }
    setMenu(null);
    ref.current?.focus();
  };

  const send = () => {
    const q = text.trim();
    if (!q || busy) return;
    onSend(q);
    setText("");
    setMenu(null);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (menu && (options.length > 0 || e.key === "Escape")) {
      if (e.key === "ArrowDown") return e.preventDefault(), setActive((a) => (a + 1) % options.length);
      if (e.key === "ArrowUp") return e.preventDefault(), setActive((a) => (a - 1 + options.length) % options.length);
      if (e.key === "Enter" || e.key === "Tab") return e.preventDefault(), choose(active);
      if (e.key === "Escape") return e.preventDefault(), setMenu(null);
    }
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      send();
    }
  };

  return (
    <form
      className="relative shrink-0 border-t border-line p-2"
      onSubmit={(e) => {
        e.preventDefault();
        send();
      }}
    >
      {menu && (
        <ul
          role="listbox"
          className="absolute inset-x-2 bottom-full mb-1 max-h-64 overflow-y-auto rounded-panel border border-line bg-panel p-1"
        >
          {menu.kind === "skill" && <li className="label-caps px-2 py-1 text-muted">{t("skillsTitle")}</li>}
          {options.length === 0 && <li className="px-2 py-1.5 text-muted">{t("mentionEmpty")}</li>}
          {options.map((o, i) => (
            <li
              key={o.key}
              role="option"
              aria-selected={i === active}
              onMouseMove={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                choose(i);
              }}
              className="flex cursor-pointer items-baseline gap-2 rounded-chip px-2 py-1.5 aria-selected:bg-panel-raised"
            >
              <span className={menu.kind === "skill" ? "num text-signal" : "text-text"}>{o.label}</span>
              <span className="min-w-0 truncate text-[11.5px] text-muted" dir="auto">
                {o.hint}
              </span>
            </li>
          ))}
        </ul>
      )}
      <div className="flex items-end gap-2 rounded-panel border border-line bg-bg p-2 focus-within:border-muted">
        <textarea
          ref={ref}
          rows={2}
          value={text}
          dir="auto"
          onChange={(e) => update(e.target.value, e.target.selectionStart)}
          onKeyDown={onKeyDown}
          onBlur={() => setTimeout(() => setMenu(null), 120)}
          placeholder={t("placeholder")}
          aria-label={t("placeholder")}
          className="max-h-40 min-h-10 flex-1 resize-none bg-transparent outline-none placeholder:text-muted"
        />
        {busy ? (
          <button
            type="button"
            onClick={onStop}
            aria-label={t("stop")}
            className="grid size-7 place-items-center rounded-panel border border-line text-text hover:bg-panel-raised"
          >
            <StopIcon />
          </button>
        ) : (
          <button
            type="submit"
            aria-label={t("send")}
            disabled={!text.trim()}
            className="grid size-7 place-items-center rounded-panel bg-signal text-signal-ink disabled:opacity-40"
          >
            <PaperPlaneIcon className="rtl:-scale-x-100" />
          </button>
        )}
      </div>
    </form>
  );
}
