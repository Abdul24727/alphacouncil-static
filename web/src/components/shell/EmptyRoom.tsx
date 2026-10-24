"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useDebateStatus } from "@/lib/debate-api";

/**
 * The 404: the advisors' room with no question before it. The seats sit in the same arc as the real
 * room (components/debate/Stage.tsx), portraits dimmed, "···" over every empty chair.
 *
 * A client component on purpose. `not-found.tsx` takes no params, so a server version would have to
 * read the locale from request headers, and with cacheComponents on that stops every route in this
 * segment from prerendering (the boundary is part of each route's shell). Here the locale and the
 * messages come from NextIntlClientProvider, which the [locale] layout has already set, and the
 * roster is fetched in the browser — so a swapped advisor is never a stale face, and a page that
 * cannot reach the API still says what went wrong and offers the way back.
 */
export function EmptyRoom() {
  const t = useTranslations("notFound");
  const { data } = useDebateStatus();
  // The API sends the advisors in seat order, then the Chair. In the room the Chair sits at the
  // head of the table, so it goes to the middle here too (Stage.tsx does the same).
  const advisors = (data?.seats ?? []).filter((s) => s.role === "advisor");
  const chair = (data?.seats ?? []).find((s) => s.role === "chair");
  const seats = [...advisors];
  if (chair) seats.splice(Math.floor(advisors.length / 2), 0, chair);
  const links: [string, string][] = [
    ["/markets", t("markets")],
    ["/screener", t("screener")],
    ["/home", t("home")],
  ];

  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-6 px-4 py-10" data-not-found>
      {/* Reserved whether or not the roster arrives, so the text does not jump when it does. */}
      <Seats seats={seats} label={t("seatsLabel")} />
      <div className="flex max-w-[46ch] flex-col items-center gap-2 text-center">
        <p className="num label-caps text-muted">404</p>
        <h1 className="headline text-[26px] leading-tight text-text">{t("heading")}</h1>
        <p className="text-text-soft">{t("body")}</p>
      </div>
      <nav className="flex flex-wrap items-center justify-center gap-2">
        {links.map(([href, label], i) => (
          <Link
            key={href}
            href={href}
            className={
              i === 0
                ? "rounded-panel bg-signal px-3 py-1.5 font-semibold text-signal-ink hover:opacity-90"
                : "rounded-panel border border-line px-3 py-1.5 text-text-soft hover:border-muted hover:text-text"
            }
          >
            {label}
          </Link>
        ))}
      </nav>
    </div>
  );
}

/**
 * The seats in the room's own arc: those nearer the middle sit higher, as round a table seen from
 * the front. Logical positions, so the order runs right to left in Arabic. Nothing moves and nothing
 * pulses: the room is not thinking, it is empty.
 */
function Seats({ seats, label }: { seats: { id: string; initials: string; portrait: string | null }[]; label: string }) {
  const n = seats.length;
  return (
    <div className="relative h-[150px] w-full max-w-[560px] overflow-x-clip" role="img" aria-label={label}>
      {seats.map((s, i) => {
        const step = i / Math.max(n - 1, 1);
        const lift = Math.sin(Math.PI * step); // 0 at the ends, 1 in the middle
        return (
          <div
            key={s.id}
            data-seat={s.id}
            className="absolute flex w-[52px] -translate-x-1/2 flex-col items-center gap-1 rtl:translate-x-1/2"
            style={{ insetInlineStart: `${(6 + 88 * step).toFixed(2)}%`, top: `${Math.round(70 - 52 * lift)}px` }}
          >
            {/* The room's own "still thinking" mark, here over a chair nobody is sitting in. */}
            <span className="num rounded-chip border border-line px-1.5 text-[12px] leading-[16px] text-muted">···</span>
            <span
              aria-hidden
              className="relative flex size-11 shrink-0 items-center justify-center overflow-hidden rounded-full border border-line bg-panel-raised opacity-40 grayscale"
            >
              {s.portrait ? (
                // eslint-disable-next-line @next/next/no-img-element -- a static public file at a fixed size
                <img src={s.portrait} alt="" width={44} height={44} className="size-full object-cover" />
              ) : (
                <span className="num text-[13px] text-text-soft">{s.initials}</span>
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
}
