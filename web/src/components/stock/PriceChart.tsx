"use client";

import {
  CandlestickSeries,
  ColorType,
  createChart,
  CrosshairMode,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  LineSeries,
  LineStyle,
  type MouseEventParams,
  type SeriesType,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useMemo, useRef, useState } from "react";
import type { components } from "@/lib/api/schema";
import { fmtCompact, fmtDate, fmtNumber, fmtPct } from "@/lib/format";
import { bollinger, ema, macd, rsi, type Series, sma } from "@/lib/indicators";

type Bar = components["schemas"]["Bar"];

export type ChartMode = "line" | "candles";
export type ChartRange = "1M" | "3M" | "6M" | "1Y" | "5Y";
export type Indicator = "sma20" | "sma50" | "sma200" | "ema20" | "rsi14" | "macd" | "bb20";

export const RANGES: ChartRange[] = ["1M", "3M", "6M", "1Y", "5Y"];
export const INDICATORS: Indicator[] = ["sma20", "sma50", "sma200", "ema20", "bb20", "rsi14", "macd"];
/** Bars an indicator needs before it has a first value (MACD: 26-day EMA plus a 9-day signal). */
export const MIN_BARS: Record<Indicator, number> = { sma20: 20, sma50: 50, sma200: 200, ema20: 20, bb20: 20, rsi14: 15, macd: 34 };

const RANGE_DAYS: Record<ChartRange, number> = { "1M": 31, "3M": 92, "6M": 183, "1Y": 366, "5Y": 1827 };

/** BRAND.md tokens, read from CSS so the chart never carries its own hex values. */
function tokens() {
  const css = getComputedStyle(document.documentElement);
  const v = (name: string) => css.getPropertyValue(`--color-${name}`).trim();
  return {
    panel: v("panel"),
    line: v("line"),
    text: v("text"),
    muted: v("muted"),
    softText: v("text-soft"),
    gain: v("gain"),
    loss: v("loss"),
    signal: v("signal"),
    stale: v("stale"),
    neutral: v("neutral-seat"),
    mono: css.getPropertyValue("--font-martian").trim() || "monospace",
  };
}

/** "#3fd98a" + 0.35 -> "rgba(63, 217, 138, 0.35)" (canvas colours, from the same tokens). */
function alpha(hex: string, a: number) {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.replace(/./g, (x) => x + x) : h, 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}

const toTime = (iso: string) => (Date.parse(`${iso}T00:00:00Z`) / 1000) as UTCTimestamp;

function lineData(times: UTCTimestamp[], values: Series) {
  const out: { time: UTCTimestamp; value: number }[] = [];
  values.forEach((v, i) => v != null && out.push({ time: times[i], value: v }));
  return out;
}

type Legend = { time: string; open: number | null; high: number | null; low: number | null; close: number; volume: number | null; change: number | null };

export function PriceChart({
  bars,
  mode,
  range,
  indicators,
  digits,
  height,
}: {
  bars: Bar[];
  mode: ChartMode;
  range: ChartRange;
  indicators: Indicator[];
  digits: number;
  height: number;
}) {
  const host = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [legend, setLegend] = useState<Legend | null>(null);
  const tl = useTranslations("stock.chart.legend");
  const tc = useTranslations("stock.chart");
  const locale = useLocale();
  const ar = locale === "ar";
  const chartLocale = ar ? "ar-u-nu-latn" : "en-US";

  const series = useMemo(() => {
    const times = bars.map((b) => toTime(b.time));
    const closes = bars.map((b) => b.close);
    return { times, closes };
  }, [bars]);

  const last = bars.length ? bars[bars.length - 1] : null;
  const lastLegend: Legend | null = last
    ? {
        time: last.time,
        open: last.open ?? null,
        high: last.high ?? null,
        low: last.low ?? null,
        close: last.close,
        volume: last.volume ?? null,
        change: bars.length > 1 ? (last.close / bars[bars.length - 2].close - 1) * 100 : null,
      }
    : null;

  useEffect(() => {
    if (!host.current || bars.length < 2) return;
    const c = tokens();
    const { times, closes } = series;
    const wantRsi = indicators.includes("rsi14");
    const wantMacd = indicators.includes("macd");

    const chart = createChart(host.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: c.panel },
        textColor: c.muted,
        fontFamily: c.mono,
        fontSize: 10.5,
        // Lightweight Charts' attribution link stays on (its licence asks for it).
        attributionLogo: true,
        panes: { separatorColor: c.line, separatorHoverColor: c.line, enableResize: false },
      },
      grid: { vertLines: { color: c.line }, horzLines: { color: c.line } },
      rightPriceScale: { borderColor: c.line },
      timeScale: { borderColor: c.line, rightOffset: 3, minBarSpacing: 0.5 },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: c.muted, labelBackgroundColor: c.line, style: LineStyle.Dashed },
        horzLine: { color: c.muted, labelBackgroundColor: c.line, style: LineStyle.Dashed },
      },
      // Month names follow the page language; digits stay Latin (BRAND.md: numbers left-to-right).
      localization: { locale: chartLocale, priceFormatter: (p: number) => fmtNumber(p, digits) ?? "" },
    });
    chartRef.current = chart;
    // The attribution link stays; only its tooltip follows the page language.
    host.current.querySelector("a[href*='tradingview.com']")?.setAttribute("title", tc("attribution"));
    const priceFormat = { type: "price" as const, precision: digits, minMove: 1 / 10 ** digits };

    // Price: candles where the bar has a full range, otherwise a stepped line.
    let main: ISeriesApi<SeriesType>;
    if (mode === "candles") {
      main = chart.addSeries(CandlestickSeries, {
        upColor: c.gain,
        downColor: c.loss,
        wickUpColor: c.gain,
        wickDownColor: c.loss,
        borderVisible: false,
        priceFormat,
        lastValueVisible: true,
        priceLineVisible: false,
      });
      main.setData(
        bars.map((b, i) =>
          b.open != null && b.high != null && b.low != null
            ? { time: times[i], open: b.open, high: b.high, low: b.low, close: b.close }
            : { time: times[i] },
        ),
      );
    } else {
      main = chart.addSeries(LineSeries, { lineWidth: 2, priceFormat, priceLineVisible: false, lastValueVisible: true });
      // BRAND.md: green on up-steps, red on down-steps. A point's colour paints the
      // segment that ends at it, so each point takes the colour of its own step.
      main.setData(
        bars.map((b, i) => ({
          time: times[i],
          value: b.close,
          color: i === 0 || b.close >= bars[i - 1].close ? c.gain : c.loss,
        })),
      );
    }

    // Volume as a faint histogram along the bottom of the price pane.
    const vol = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      lastValueVisible: false,
      priceLineVisible: false,
    });
    vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    vol.setData(
      bars.map((b, i) => ({
        time: times[i],
        value: b.volume ?? 0,
        color: alpha(i === 0 || b.close >= bars[i - 1].close ? c.gain : c.loss, 0.35),
      })),
    );

    const overlay = (values: Series, color: string, style = LineStyle.Solid) => {
      const s = chart.addSeries(LineSeries, {
        color,
        lineWidth: 1,
        lineStyle: style,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
        priceFormat,
      });
      s.setData(lineData(times, values));
    };
    if (indicators.includes("sma20")) overlay(sma(closes, 20), c.softText);
    if (indicators.includes("sma50")) overlay(sma(closes, 50), c.signal);
    if (indicators.includes("sma200")) overlay(sma(closes, 200), c.stale);
    if (indicators.includes("ema20")) overlay(ema(closes, 20), c.text, LineStyle.Dotted);
    if (indicators.includes("bb20")) {
      const b = bollinger(closes, 20, 2);
      overlay(b.upper, c.muted, LineStyle.Dashed);
      overlay(b.mid, c.neutral, LineStyle.Dotted);
      overlay(b.lower, c.muted, LineStyle.Dashed);
    }

    let pane = 1;
    if (wantRsi) {
      const s = chart.addSeries(
        LineSeries,
        { color: c.softText, lineWidth: 1, priceLineVisible: false, lastValueVisible: true, priceFormat: { type: "price", precision: 1, minMove: 0.1 } },
        pane,
      );
      s.setData(lineData(times, rsi(closes, 14)));
      for (const level of [30, 70]) s.createPriceLine({ price: level, color: c.line, lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: "" });
      pane++;
    }
    if (wantMacd) {
      const m = macd(closes);
      const hist = chart.addSeries(HistogramSeries, { priceLineVisible: false, lastValueVisible: false, priceFormat }, pane);
      hist.setData(
        m.hist.flatMap((v, i) =>
          v == null ? [] : [{ time: times[i], value: v, color: alpha(v >= 0 ? c.gain : c.loss, 0.55) }],
        ),
      );
      const lineS = chart.addSeries(LineSeries, { color: c.text, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, priceFormat }, pane);
      lineS.setData(lineData(times, m.line));
      const sig = chart.addSeries(LineSeries, { color: c.signal, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, priceFormat }, pane);
      sig.setData(lineData(times, m.signal));
    }

    // Price pane takes most of the height; RSI and MACD share the rest.
    const panes = chart.panes();
    panes[0]?.setStretchFactor(panes.length > 1 ? 3.2 : 1);
    for (let i = 1; i < panes.length; i++) panes[i].setStretchFactor(1);

    // Visible window: the selected range ending at the last bar.
    const lastTime = times[times.length - 1];
    const from = (lastTime - RANGE_DAYS[range] * 86400) as UTCTimestamp;
    chart.timeScale().setVisibleRange({ from: Math.max(from, times[0]) as Time, to: lastTime as Time });

    const byTime = new Map(bars.map((b, i) => [times[i] as number, i]));
    const onMove = (p: MouseEventParams) => {
      const i = p.time != null ? byTime.get(p.time as number) : undefined;
      if (i == null) return setLegend(null);
      const b = bars[i];
      setLegend({
        time: b.time,
        open: b.open ?? null,
        high: b.high ?? null,
        low: b.low ?? null,
        close: b.close,
        volume: b.volume ?? null,
        change: i > 0 ? (b.close / bars[i - 1].close - 1) * 100 : null,
      });
    };
    chart.subscribeCrosshairMove(onMove);

    return () => {
      chart.unsubscribeCrosshairMove(onMove);
      chart.remove();
      chartRef.current = null;
    };
  }, [bars, series, mode, range, indicators, digits, height, chartLocale, tc]);

  const shown = legend ?? lastLegend;
  return (
    <div className="relative" style={{ height }}>
      <div ref={host} className="absolute inset-0" data-chart="price" data-bars={bars.length} />
      {shown && (
        // Between the left edge and the price scale in both languages; reads in the page's direction.
        <div className="pointer-events-none absolute top-1.5 right-16 left-2 z-10 flex flex-wrap gap-x-3 text-[10.5px]" dir={ar ? "rtl" : "ltr"}>
          <span className="num text-muted">{fmtDate(shown.time, locale)}</span>
          {shown.open != null && <LegendValue label={tl("open")} value={fmtNumber(shown.open, digits)} />}
          {shown.high != null && <LegendValue label={tl("high")} value={fmtNumber(shown.high, digits)} />}
          {shown.low != null && <LegendValue label={tl("low")} value={fmtNumber(shown.low, digits)} />}
          <LegendValue label={tl("close")} value={fmtNumber(shown.close, digits)} />
          {shown.change != null && (
            <span className={`num ${shown.change >= 0 ? "text-gain" : "text-loss"}`}>{fmtPct(shown.change, 2, true)}</span>
          )}
          {shown.volume != null && <LegendValue label={tl("volume")} value={fmtCompact(shown.volume)} />}
        </div>
      )}
      {/* An indicator the history is too short for draws nothing: say so instead. */}
      {indicators.some((i) => bars.length < MIN_BARS[i]) && (
        <p className="pointer-events-none absolute right-16 bottom-7 left-2 z-10 text-[11px] text-stale" data-indicator-note>
          {indicators
            .filter((i) => bars.length < MIN_BARS[i])
            .map((i) => tc("notEnough", { name: tc(`indicators.${i}`), need: String(MIN_BARS[i]), have: String(bars.length) }))
            .join(" ")}
        </p>
      )}
    </div>
  );
}

function LegendValue({ label, value }: { label: string; value: string | null }) {
  // A flex pair keeps each label beside its own number in either direction.
  return (
    <span className="inline-flex items-baseline gap-1">
      <span className="text-muted">{label}</span>
      <span className="num text-text">{value}</span>
    </span>
  );
}
