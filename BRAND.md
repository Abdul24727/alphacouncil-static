# BRAND.md — AlphaCouncil · Ras Tanura

Every page and every Claude Code session follows this file. Anything it bans is a bug.

AlphaCouncil is a dense research terminal for Gulf markets: safety orange on graphite.

## Colors

| Token | Hex | Use |
| --- | --- | --- |
| `bg` | #0C0D10 | Page background (graphite) |
| `panel` | #14161B | Panels, inputs |
| `panel-raised` | #1D2028 | Hover, selected rows, user chat bubbles |
| `line` | #272B34 | All borders and dividers, 1px |
| `text` | #ECEEF2 | Primary text |
| `text-soft` | #B8BECA | Body copy on the landing page |
| `muted` | #9299A8 | Labels, timestamps, secondary text |
| `signal` | #FF6A1A | The ONE brand color: primary buttons, active tab, ticker group 1, links |
| `signal-ink` | #170800 | Text on orange buttons |
| `gain` | #3FD98A | Price up, positive change, fresh-data light |
| `loss` | #FF4D5E | Price down, negative change, bearish seat |
| `stale` | #F2B134 | Data older than its expected update |
| `neutral-seat` | #4A505C | Neutral council seat |

In code these live in `web/src/app/globals.css` as CSS variables (`--color-<token>`) and Tailwind theme colors (`bg-panel`, `text-muted`, `border-line`, …). Never write a raw hex in a component.

## Type

- Archivo for all words. Headlines: weight 700–800, condensed (font-stretch 80–85%), uppercase only on landing-page section titles.
- Martian Mono for every number, ticker, timestamp and small label in caps (letter-spacing 0.08em).
- Arabic: a matching Arabic face is still open (see Open items); never fall back to the browser default.
- Sizes: 13px app body, 15.5–18px landing body, 22px panel titles, clamp(48px, 7vw, 104px) landing hero.

## Shape and spacing

- Radius 6px on panels and buttons, 4px on chips. Gap 10–12px between panels. Panel padding 12px.
- Every panel header: freshness light · group color · title · add-to-Copilot · full screen · menu.
- Charts: price line green on up-steps, red on down-steps; grid lines in `line`; no gradients.

## Banned (these made the old site look generic)

- Teal, purple, any gradient text or gradient background, glow effects
- Emoji, including flag emoji
- Icon-in-a-rounded-box cards and grids of identical feature cards
- Small uppercase eyebrow labels above every heading (“THE PROBLEM”, “FEATURES”)
- Fake browser dots on mockups; repeated stat-chip rows
- Inter, Roboto, Arial, system-ui as visible fonts
- Any number on screen that is not from the database (use a labelled placeholder instead)

## Open items

| Item | Status |
| --- | --- |
| Arabic face | Archivo has no Arabic letters. Phase 1 candidate: IBM Plex Sans Arabic, loaded as the Arabic fallback inside the Archivo stack. Confirm or replace before Phase 7. |
