"use client";

import { useChat } from "@ai-sdk/react";
import { Cross2Icon, EnterFullScreenIcon, ExitFullScreenIcon, PlusIcon } from "@radix-ui/react-icons";
import { useQuery } from "@tanstack/react-query";
import { DefaultChatTransport } from "ai";
import { useTranslations } from "next-intl";
import { Tooltip } from "radix-ui";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { Composer } from "@/components/copilot/Composer";
import { AssistantMessage, UserMessage } from "@/components/copilot/Message";
import type { CopilotMessage } from "@/components/copilot/types";
import { Link } from "@/i18n/navigation";
import { api, unwrap } from "@/lib/api/client";
import { useMe } from "@/lib/auth";
import { attachedWithData, useCopilot } from "@/lib/copilot-store";
import { useLayout } from "@/lib/layout-store";
import { revealPanel } from "@/lib/panel-registry";
import { useTickerGroups } from "@/lib/ticker-groups";
import { Kbd } from "./Kbd";
import { ResizeHandle } from "./ResizeHandle";
import { WithPathname } from "./WithPathname";

/**
 * Right-hand Copilot (left in Arabic). Answers use only attached panels and
 * database tools, cite the panel they used, and stream from /api/v1/copilot/chat.
 */
export function CopilotPane() {
  const t = useTranslations("copilot");
  const mobileOpen = useLayout((s) => s.mobileCopilotOpen);
  // useChat creates random ids, which Cache Components forbids during prerender:
  // the chat mounts in the browser only, behind a static frame with the same header.
  const mounted = useSyncExternalStore(subscribeNever, () => true, () => false);

  return (
    <aside
      aria-label={t("title")}
      data-copilot-pane
      className={`relative flex w-[var(--copilot-w)] shrink-0 flex-col border-s border-line bg-panel md:copilot-closed:hidden md:copilot-full:w-auto md:copilot-full:flex-1 ${
        mobileOpen ? "max-md:fixed max-md:inset-0 max-md:z-40 max-md:w-full" : "max-md:hidden"
      }`}
    >
      {mounted ? (
        <CopilotBody />
      ) : (
        <header className="flex h-12 shrink-0 items-center border-b border-line ps-3">
          <h2 className="headline text-[17px] leading-none">{t("title")}</h2>
        </header>
      )}
      <ResizeHandle pane="copilot" className="start-[-3px] max-md:hidden copilot-full:hidden" />
    </aside>
  );
}

const subscribeNever = () => () => {};

const CONVERSATION_KEY = "ac-copilot-conversation";

function loadConversation(): CopilotMessage[] {
  try {
    return JSON.parse(sessionStorage.getItem(CONVERSATION_KEY) ?? "[]") as CopilotMessage[];
  } catch {
    return [];
  }
}

function saveConversation(messages: CopilotMessage[]) {
  try {
    sessionStorage.setItem(CONVERSATION_KEY, JSON.stringify(messages));
  } catch {
    // Storage full or blocked: the conversation just does not survive a reload.
  }
}

/** The API's `detail` rather than its JSON envelope; known codes come back as a message key. */
function errorDetail(error: Error): { code: "sign_in_required" | "rate_limited" } | { text: string } {
  try {
    const detail = (JSON.parse(error.message) as { detail?: unknown }).detail;
    if (detail === "sign_in_required" || detail === "rate_limited") return { code: detail };
    return { text: typeof detail === "string" ? detail : error.message };
  } catch {
    return { text: error.message };
  }
}

function ErrorLine({ error }: { error: Error }) {
  const t = useTranslations("copilot");
  const d = errorDetail(error);
  return <p className="text-loss">{"code" in d ? t(`errors.${d.code}`) : t("error", { message: d.text })}</p>;
}

function CopilotBody() {
  const t = useTranslations("copilot");
  const fullscreen = useLayout((s) => s.copilotFullscreen);
  const toggleCopilot = useLayout((s) => s.toggleCopilot);
  const toggleFullscreen = useLayout((s) => s.toggleCopilotFullscreen);
  const setMobileOpen = useLayout((s) => s.setMobileCopilotOpen);
  const attached = useCopilot((s) => s.attached);
  const detach = useCopilot((s) => s.detach);

  // The transport reads attached panels and the page ticker at send time.
  const [transport] = useState(
    () =>
      new DefaultChatTransport<CopilotMessage>({
        api: "/api/v1/copilot/chat",
        prepareSendMessagesRequest: ({ id, messages }) => ({
          body: {
            id,
            messages: messages.slice(-13),
            panels: attachedWithData(),
            // <html lang> follows the [locale] segment, so it is the UI language at send time.
            locale: document.documentElement.lang === "ar" ? "ar" : "en",
            ticker: useTickerGroups.getState().tickers[1] ?? null,
          },
        }),
      }),
  );
  // The conversation survives a language switch (which remounts the shell) for this tab.
  const [saved] = useState(loadConversation);
  const { messages, sendMessage, status, stop, setMessages, error } = useChat<CopilotMessage>({ transport, messages: saved });
  const busy = status === "submitted" || status === "streaming";
  useEffect(() => {
    if (status === "ready" || status === "error") saveConversation(messages);
  }, [messages, status]);
  const me = useMe();

  const modelStatus = useQuery({
    queryKey: ["copilot", "status"],
    queryFn: async () => unwrap(await api.GET("/v1/copilot/status")),
    staleTime: 5 * 60_000,
  });
  const standIn = modelStatus.data?.stand_in;
  const needsSignIn = !!modelStatus.data?.sign_in_required && !me.isPending && !me.data;

  // Keep the newest content in view while an answer streams.
  const scroller = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const close = () => {
    if (window.matchMedia("(max-width: 767px)").matches) setMobileOpen(false);
    else toggleCopilot();
  };
  const ask = (text: string) => void sendMessage({ text });

  return (
    <>
      <header className="flex h-12 shrink-0 items-center gap-2 border-b border-line ps-3 pe-2">
        <h2 className="headline text-[17px] leading-none">{t("title")}</h2>
        {standIn !== undefined && (
          <span
            title={standIn ? t("standInTip") : t("model", { name: modelStatus.data?.model ?? "" })}
            className={`label-caps rounded-chip border px-1 ${standIn ? "border-stale/50 text-stale" : "border-line text-muted"}`}
          >
            {standIn ? t("standIn") : modelStatus.data?.model}
          </span>
        )}
        <div className="ms-auto flex items-center gap-0.5">
          <IconButton label={t("clear")} onClick={() => setMessages([])}>
            <PlusIcon />
          </IconButton>
          <IconButton label={fullscreen ? t("exitFullscreen") : t("fullscreen")} onClick={toggleFullscreen} className="max-md:hidden">
            {fullscreen ? <ExitFullScreenIcon /> : <EnterFullScreenIcon />}
          </IconButton>
          <IconButton label={t("close")} shortcut="L" onClick={close}>
            <Cross2Icon />
          </IconButton>
        </div>
      </header>

      <section aria-label={t("context")} className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-line px-3 py-2">
        <span className="label-caps text-muted">{t("context")}</span>
        {attached.length === 0 ? (
          <span className="text-muted">{t("noContext")} · {t("attachHint")}</span>
        ) : (
          attached.map((p) => (
            <span key={p.id} data-context-chip={p.id} className="flex items-center gap-1 rounded-chip border border-line bg-panel-raised ps-1.5 pe-0.5">
              <button type="button" onClick={() => revealPanel(p.id)} className="max-w-36 truncate text-text" title={p.title}>
                {p.title}
              </button>
              {p.ticker && <span className="num text-[10.5px] text-muted">{p.ticker}</span>}
              <button
                type="button"
                aria-label={t("detach", { title: p.title })}
                onClick={() => detach(p.id)}
                className="grid size-4 place-items-center rounded-[2px] text-muted hover:text-text"
              >
                <Cross2Icon className="size-3" />
              </button>
            </span>
          ))
        )}
      </section>

      <div ref={scroller} className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-3" aria-live="polite">
        {messages.length === 0 ? (
          <div className="mt-auto flex flex-col gap-2">
            <p className="max-w-[40ch] text-muted">{t("intro")}</p>
            <div className="flex flex-col items-start gap-1">
              {(t.raw("examples") as string[]).map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => ask(q)}
                  className="rounded-chip border border-line px-2 py-1 text-start text-text-soft hover:border-signal/50 hover:text-text"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) =>
            m.role === "user" ? (
              <UserMessage key={m.id} message={m} />
            ) : (
              <AssistantMessage key={m.id} message={m} streaming={busy && i === messages.length - 1} onFollowUp={ask} />
            ),
          )
        )}
        {error && <ErrorLine error={error} />}
      </div>

      {needsSignIn ? (
        <p className="shrink-0 border-t border-line p-3 text-text-soft" data-copilot-signin>
          {t("signIn")}{" "}
          <WithPathname
            render={(pathname) => (
              <Link href={`/login?next=${encodeURIComponent(pathname ?? "/home")}`} className="text-signal hover:underline">
                {t("signInLink")}
              </Link>
            )}
          />
        </p>
      ) : (
        <Composer busy={busy} onSend={ask} onStop={() => void stop()} />
      )}
    </>
  );
}

function IconButton({
  label,
  shortcut,
  onClick,
  className = "",
  children,
}: {
  label: string;
  shortcut?: string;
  onClick: () => void;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <button
          type="button"
          aria-label={label}
          onClick={onClick}
          className={`grid size-7 place-items-center rounded-panel text-muted hover:bg-panel-raised hover:text-text ${className}`}
        >
          {children}
        </button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content sideOffset={6} className="z-50 flex items-center gap-2 rounded-chip border border-line bg-panel-raised px-2 py-1 text-text">
          {label}
          {shortcut && <Kbd k={shortcut} />}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
