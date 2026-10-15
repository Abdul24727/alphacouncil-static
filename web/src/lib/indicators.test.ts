// Run with: npm test   (Node's built-in runner; Node 24 strips the types)
import assert from "node:assert/strict";
import { test } from "node:test";
import { bollinger, ema, macd, rsi, sma } from "./indicators.ts";

const close = (a: number, b: number) => Math.abs(a - b) < 1e-9;

test("sma: undefined until the window is full", () => {
  assert.deepEqual(sma([1, 2, 3, 4, 5], 3), [null, null, 2, 3, 4]);
});

test("ema: seeded with the SMA, then 2/(n+1) weighting", () => {
  const e = ema([1, 2, 3, 4, 5], 3);
  assert.deepEqual(e.slice(0, 2), [null, null]);
  assert.equal(e[2], 2);
  assert.ok(close(e[3]!, 3));
  assert.ok(close(e[4]!, 4));
});

test("rsi: all gains is 100, all losses is 0, flat-up-down is 50", () => {
  const up = Array.from({ length: 20 }, (_, i) => 10 + i);
  const down = Array.from({ length: 20 }, (_, i) => 30 - i);
  assert.equal(rsi(up, 14)[19], 100);
  assert.equal(rsi(down, 14)[19], 0);
  const zigzag = Array.from({ length: 30 }, (_, i) => (i % 2 ? 11 : 10));
  assert.ok(Math.abs(rsi(zigzag, 14)[29]! - 50) < 5);
  assert.equal(rsi(up, 14)[13], null);
});

test("macd: zero on a flat series; signal starts after the slow EMA plus the signal window", () => {
  const flat = new Array(60).fill(5);
  const m = macd(flat);
  assert.equal(m.line[24], null);
  assert.equal(m.line[25], 0);
  assert.equal(m.signal[25 + 7], null);
  assert.equal(m.signal[25 + 8], 0);
  assert.equal(m.hist[59], 0);
});

test("bollinger: bands collapse on a flat series and widen with variance", () => {
  const flat = bollinger(new Array(25).fill(7), 20, 2);
  assert.equal(flat.upper[24], 7);
  assert.equal(flat.lower[24], 7);
  const b = bollinger([1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3], 20, 2);
  assert.equal(b.mid[19], 2);
  assert.equal(b.upper[19], 4);
  assert.equal(b.lower[19], 0);
});
