"use client";

import { Cross2Icon, PlusIcon } from "@radix-ui/react-icons";
import { useLocale, useTranslations } from "next-intl";
import { Popover } from "radix-ui";
import { useState } from "react";
import { ChangeCell, PriceCell, TickerCell, TickerRow, Th, useExchangeName } from "@/components/market/shared";
import { Panel, PanelUnavailable } from "@/components/panel/Panel";
import { Num, priceDigits, QueryState, toTsv } from "@/components/stock/common";
import { TickerPicker } from "@/components/ticker/TickerPicker";
import { Link } from "@/i18n/navigation";
import { ApiError, type TickerHit } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useMe } from "@/lib/auth";
import { currencyLabel, fmtDate, fmtNumber, fmtPct, signClass, withCurrency } from "@/lib/format";
import { useAlerts, usePortfolio, usePortfolioMutations } from "@/lib/queries-app";

type Portfolio = components["schemas"]["Portfolio"];

export function PortfolioView() {
  const t = useTranslations("portfolio");
  const ta = useTranslations("auth");
  const me = useMe();
  const signedIn = !!me.data;
  const p = usePortfolio(signedIn);
  const a = useAlerts(signedIn);

  if (me.isPending) return <div className="p-2.5" />;
  if (!signedIn) {
    return (
      <div className="p-2.5">
        <section className="flex flex-col items-start gap-3 rounded-panel border border-line bg-panel p-4" data-signin-prompt>
          <p className="text-text-soft">{ta("required")}</p>
          <div className="flex gap-2">
            <Link href="/signup?next=/portfolio" className="rounded-panel bg-signal px-3 py-1.5 font-semibold text-signal-ink">
              {ta("signupLink")}
            </Link>
            <Link href="/login?next=/portfolio" className="rounded-panel border border-line px-3 py-1.5 text-text hover:bg-panel-raised">
              {ta("signIn")}
            </Link>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="@container min-h-0 flex-1 overflow-y-auto">
      <div className="grid grid-cols-12 gap-2.5 p-2.5">
        <HoldingsPanel portfolio={p.data} isPending={p.isPending} error={p.error} refetch={() => p.refetch()} />
        <ExposurePanel portfolio={p.data} isPending={p.isPending} error={p.error} />
        <CouncilPanel portfolio={p.data} isPending={p.isPending} error={p.error} />
        <AlertsPanel alerts={a.data} isPending={a.isPending} error={a.error} />
      </div>
      <p className="px-3 pb-3 text-[12px] text-muted">{t("note")}</p>
    </div>
  );
}

function AddHolding() {
  const t = useTranslations("portfolio");
  const { upsert } = usePortfolioMutations();
  const [pick, setPick] = useState<TickerHit | null>(null);
  const [open, setOpen] = useState(false);
  const [qty, setQty] = useState("");
  const [cost, setCost] = useState("");
  const [error, setError] = useState<string | null>(null);
  const input = "h-8 rounded-panel border border-line bg-bg px-2 text-text outline-none focus:border-muted";

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const quantity = Number(qty);
    if (!pick || !(quantity > 0)) return setError(t("errors.input"));
    try {
      await upsert.mutateAsync({ ticker: pick.slug, quantity, avg_cost: cost ? Number(cost) : null });
      setPick(null);
      setQty("");
      setCost("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.input"));
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-2 border-b border-line p-2" data-add-holding>
      <Popover.Root open={open} onOpenChange={setOpen}>
        <Popover.Trigger asChild>
          <button type="button" className={`${input} min-w-48 text-start`} data-holding-ticker>
            {pick ? (
              <span>
                <span className="num me-2 text-[12px]">{pick.symbol}</span>
                {pick.name_en ?? pick.name_ar}
              </span>
            ) : (
              <span className="text-muted">{t("pickTicker")}</span>
            )}
          </button>
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content align="start" sideOffset={4} className="z-50 flex w-[min(380px,calc(100vw-24px))] flex-col overflow-hidden rounded-panel border border-line bg-panel">
            <TickerPicker
              compact
              onPick={(hit) => {
                setPick(hit);
                setOpen(false);
              }}
            />
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
      <label className="flex flex-col gap-0.5">
        <span className="label-caps text-muted">{t("quantity")}</span>
        <input className={`${input} num w-24`} inputMode="decimal" value={qty} onChange={(e) => setQty(e.target.value)} data-holding-qty />
      </label>
      <label className="flex flex-col gap-0.5">
        <span className="label-caps text-muted">{t("avgCost")}</span>
        <input className={`${input} num w-24`} inputMode="decimal" value={cost} onChange={(e) => setCost(e.target.value)} />
      </label>
      <button type="submit" disabled={upsert.isPending} className="flex h-8 items-center gap-1 rounded-panel bg-signal px-3 font-semibold text-signal-ink disabled:opacity-50">
        <PlusIcon />
        {t("add")}
      </button>
      {error && <span className="text-loss">{error}</span>}
    </form>
  );
}

function HoldingsPanel({ portfolio: p, isPending, error, refetch }: { portfolio?: Portfolio; isPending: boolean; error: unknown; refetch: () => void }) {
  const t = useTranslations("portfolio");
  const locale = useLocale();
  const { remove } = usePortfolioMutations();
  const holdings = p?.holdings ?? [];

  return (
    <Panel
      id="portfolio.holdings"
      title={t("holdings")}
      onRefresh={refetch}
      copyData={() =>
        toTsv([
          ["symbol", "quantity", "avg_cost", "close", "change_pct", "market_value", "pnl", "pnl_pct", "currency"],
          ...holdings.map((h) => [h.ticker.symbol, h.quantity, h.avg_cost, h.price.close, h.price.change_pct, h.market_value, h.pnl, h.pnl_pct, h.ticker.currency]),
        ])
      }
      copilotData={() => p}
      className="col-span-12"
      bodyClassName="p-0"
    >
      <AddHolding />
      <div className="overflow-x-auto p-2">
        <QueryState isPending={isPending} error={error} empty={!!p && holdings.length === 0} emptyText={t("empty")} rows={4}>
          <table className="w-full min-w-[760px]">
            <thead>
              <tr>
                <Th>{t("cols.ticker")}</Th>
                <Th end>{t("cols.quantity")}</Th>
                <Th end>{t("cols.price")}</Th>
                <Th end>{t("cols.change")}</Th>
                <Th end>{t("cols.value")}</Th>
                <Th end>{t("cols.weight")}</Th>
                <Th end>{t("cols.pnl")}</Th>
                <Th end>{t("cols.asOf")}</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => (
                <TickerRow key={h.id} ticker={h.ticker}>
                  <td className="py-1.5 pe-2">
                    <TickerCell ticker={h.ticker} />
                  </td>
                  <td className="num py-1.5 text-end">{fmtNumber(h.quantity, h.quantity % 1 ? 2 : 0)}</td>
                  <td className="py-1.5 text-end">
                    <PriceCell price={h.price} currency={h.ticker.currency} />
                  </td>
                  <td className="py-1.5 text-end">
                    <ChangeCell value={h.price.change_pct} />
                  </td>
                  <td className="py-1.5 text-end">
                    <Num value={withCurrency(fmtNumber(h.market_value, 0), h.ticker.currency, locale)} />
                  </td>
                  <td className="py-1.5 text-end">
                    <Num value={fmtPct(h.weight_pct, 1)} />
                  </td>
                  <td className="py-1.5 text-end">
                    {h.pnl != null ? (
                      <span className={`num ${signClass(h.pnl)}`}>
                        {fmtNumber(h.pnl, 0)} · {fmtPct(h.pnl_pct, 1, true)}
                      </span>
                    ) : (
                      <span className="label-caps text-muted" title={t("noCost")}>—</span>
                    )}
                  </td>
                  <td className="num py-1.5 text-end text-[11.5px] text-muted">{fmtDate(h.price.as_of, locale) ?? "—"}</td>
                  <td className="py-1.5 text-end">
                    <button
                      type="button"
                      aria-label={t("remove", { symbol: h.ticker.symbol })}
                      onClick={(e) => {
                        e.stopPropagation();
                        remove.mutate(h.id);
                      }}
                      className="grid size-6 place-items-center rounded-panel text-muted hover:bg-panel-raised hover:text-loss"
                    >
                      <Cross2Icon />
                    </button>
                  </td>
                </TickerRow>
              ))}
            </tbody>
          </table>
        </QueryState>
      </div>
    </Panel>
  );
}

function Bars({ slices, locale }: { slices: { label: string; label_ar?: string | null; weight_pct: number }[]; locale: string }) {
  const name = useExchangeName();
  return (
    <ul className="flex flex-col gap-1.5">
      {slices.map((s) => (
        <li key={s.label} className="grid grid-cols-[minmax(0,9rem)_1fr_3.5rem] items-center gap-2">
          <span className="truncate text-text-soft">{locale === "ar" ? (s.label_ar ?? name(s.label)) : name(s.label)}</span>
          <span className="h-1.5 overflow-hidden rounded-full bg-line">
            <span className="block h-full bg-signal" style={{ width: `${s.weight_pct}%` }} />
          </span>
          <span className="num text-end text-[11.5px]">{fmtPct(s.weight_pct, 1)}</span>
        </li>
      ))}
    </ul>
  );
}

function ExposurePanel({ portfolio: p, isPending, error }: { portfolio?: Portfolio; isPending: boolean; error: unknown }) {
  const t = useTranslations("portfolio");
  const locale = useLocale();
  const groups = p?.groups ?? [];
  return (
    <Panel
      id="portfolio.exposure"
      title={t("exposure")}
      copyData={() => toTsv(groups.flatMap((g) => [...g.sectors, ...g.exchanges].map((s) => [g.currency, s.label, s.value, s.weight_pct])))}
      copilotData={() => groups}
      className="col-span-12 @4xl:col-span-6"
    >
      <QueryState isPending={isPending} error={error} empty={!!p && groups.length === 0} emptyText={t("emptyShort")}>
        <div className="flex flex-col gap-4">
          {groups.length > 1 && <p className="text-[12px] text-muted">{t("perCurrency")}</p>}
          {groups.map((g) => (
            <section key={g.currency} aria-label={g.currency}>
              <header className="mb-2 flex items-baseline justify-between border-b border-line pb-1">
                <span className="label-caps text-muted">{currencyLabel(g.currency, locale)}</span>
                <span className="num">
                  {fmtNumber(g.market_value, 0)} <span className={signClass(g.day_change_value)}>{g.day_change_value >= 0 ? "+" : ""}{fmtNumber(g.day_change_value, 0)}</span>
                </span>
              </header>
              <div className="grid grid-cols-1 gap-4 @2xl:grid-cols-2">
                <div>
                  <h3 className="label-caps mb-1.5 text-muted">{t("bySector")}</h3>
                  <Bars slices={g.sectors} locale={locale} />
                </div>
                <div>
                  <h3 className="label-caps mb-1.5 text-muted">{t("byMarket")}</h3>
                  <Bars slices={g.exchanges} locale={locale} />
                </div>
              </div>
            </section>
          ))}
        </div>
      </QueryState>
    </Panel>
  );
}

function CouncilPanel({ portfolio: p, isPending, error }: { portfolio?: Portfolio; isPending: boolean; error: unknown }) {
  const t = useTranslations("portfolio");
  const tc = useTranslations("stock.council");
  const seats = p?.council ?? [];
  return (
    <Panel
      id="portfolio.council"
      title={t("council")}
      copyData={() => toTsv(seats.map((s) => [s.seat, s.bullish, s.neutral, s.bearish, s.abstain]))}
      copilotData={() => seats}
      className="col-span-12 @4xl:col-span-6"
    >
      <QueryState isPending={isPending} error={error} empty={!!p && p.holdings.length === 0} emptyText={t("emptyShort")}>
        <p className="mb-2 text-[12px] text-muted">{t("councilNote")}</p>
        <ul className="flex flex-col gap-2">
          {seats.map((s) => {
            const total = s.bullish + s.neutral + s.bearish + s.abstain || 1;
            return (
              <li key={s.seat} className="grid grid-cols-[6rem_1fr_auto] items-center gap-2">
                <span className="text-text-soft">{tc(`seats.${s.seat}`)}</span>
                <span className="flex h-2 overflow-hidden rounded-full bg-line" aria-hidden>
                  <span className="bg-gain" style={{ width: `${(s.bullish / total) * 100}%` }} />
                  <span className="bg-neutral-seat" style={{ width: `${(s.neutral / total) * 100}%` }} />
                  <span className="bg-loss" style={{ width: `${(s.bearish / total) * 100}%` }} />
                </span>
                <span className="num text-[11px] text-muted" aria-label={`${tc("bullish")} ${s.bullish}, ${tc("neutral")} ${s.neutral}, ${tc("bearish")} ${s.bearish}, ${tc("abstain")} ${s.abstain}`}>
                  <span className="text-gain">{s.bullish}</span>·{s.neutral}·<span className="text-loss">{s.bearish}</span>
                  {s.abstain ? <span> ({s.abstain})</span> : null}
                </span>
              </li>
            );
          })}
        </ul>
      </QueryState>
    </Panel>
  );
}

function AlertsPanel({ alerts, isPending, error }: { alerts?: components["schemas"]["Alert"][]; isPending: boolean; error: unknown }) {
  const t = useTranslations("portfolio");
  const { addAlert, removeAlert } = usePortfolioMutations();
  const [pick, setPick] = useState<TickerHit | null>(null);
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<"above" | "below">("above");
  const [price, setPrice] = useState("");
  const input = "h-8 rounded-panel border border-line bg-bg px-2 text-text outline-none focus:border-muted";

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pick || !(Number(price) > 0)) return;
    addAlert.mutate({ ticker: pick.slug, kind, price: Number(price) }, { onSuccess: () => setPrice("") });
  };

  return (
    <Panel
      id="portfolio.alerts"
      title={t("alerts")}
      copyData={() => toTsv((alerts ?? []).map((x) => [x.ticker.symbol, x.kind, x.price, x.last.close, x.triggered]))}
      copilotData={() => alerts}
      className="col-span-12"
      bodyClassName="p-0"
    >
      <form onSubmit={submit} className="flex flex-wrap items-end gap-2 border-b border-line p-2">
        <Popover.Root open={open} onOpenChange={setOpen}>
          <Popover.Trigger asChild>
            <button type="button" className={`${input} min-w-40 text-start`}>
              {pick ? <span className="num text-[12px]">{pick.symbol}</span> : <span className="text-muted">{t("pickTicker")}</span>}
            </button>
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content align="start" sideOffset={4} className="z-50 flex w-[min(380px,calc(100vw-24px))] flex-col overflow-hidden rounded-panel border border-line bg-panel">
              <TickerPicker compact onPick={(hit) => (setPick(hit), setOpen(false))} />
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
        <select className={input} value={kind} onChange={(e) => setKind(e.target.value as "above" | "below")} aria-label={t("when")}>
          <option value="above">{t("above")}</option>
          <option value="below">{t("below")}</option>
        </select>
        <input className={`${input} num w-24`} inputMode="decimal" placeholder={t("price")} value={price} onChange={(e) => setPrice(e.target.value)} aria-label={t("price")} />
        <button type="submit" className="flex h-8 items-center gap-1 rounded-panel border border-line px-3 text-text hover:bg-panel-raised">
          <PlusIcon />
          {t("addAlert")}
        </button>
      </form>
      <div className="p-2">
        <QueryState isPending={isPending} error={error} empty={!!alerts && alerts.length === 0} emptyText={t("noAlerts")}>
          <table className="w-full">
            <tbody>
              {(alerts ?? []).map((x) => (
                <tr key={x.id} className="border-t border-line first:border-t-0">
                  <td className="py-1.5">
                    <TickerCell ticker={x.ticker} />
                  </td>
                  <td className="py-1.5 text-text-soft">
                    {t(x.kind)} <span className="num">{fmtNumber(x.price, priceDigits(x.ticker.currency))}</span>
                  </td>
                  <td className="py-1.5 text-end">
                    <PriceCell price={x.last} currency={x.ticker.currency} />
                  </td>
                  <td className="py-1.5 text-end">
                    {x.triggered == null ? (
                      <PanelUnavailable />
                    ) : (
                      <span className={`label-caps ${x.triggered ? "text-signal" : "text-muted"}`}>{x.triggered ? t("triggered") : t("waiting")}</span>
                    )}
                  </td>
                  <td className="w-8 py-1.5 text-end">
                    <button type="button" aria-label={t("removeAlert")} onClick={() => removeAlert.mutate(x.id)} className="grid size-6 place-items-center rounded-panel text-muted hover:text-loss">
                      <Cross2Icon />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryState>
      </div>
    </Panel>
  );
}
