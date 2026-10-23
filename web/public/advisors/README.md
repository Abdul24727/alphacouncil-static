# Advisor portraits

Caricature portraits for the advisors' debate room, supplied by the owner. Until a seat's portrait is here and named
in its file (`api/app/advisors/<id>.md`, `portrait: <file>`), the screen shows the seat's initials on a graphite disc.

- One file per seat, named after the seat id: `buffett.webp`, `lynch.webp`, `dalio.webp`, `marks.webp`,
  `alwaleed.webp`, `alrajhi.webp`, `chair.webp` (all seven in place since 2026-10-23: 512 × 512 WebP made from the
  owner's 1024 px images, kept in `docs/advisors-portraits/originals/`). A named file that fails to load also
  falls back to the initials.
- Square, at least 512 × 512 px, WebP or PNG, under 200 KB. Head and shoulders, centred, facing the camera.
- Background transparent or the brand graphite (#14161B). BRAND.md applies: no gradients, glows, teal or purple.
- Drawn as caricatures, so nobody mistakes a seat for the real person (the screen's disclaimer says the same).

Everything in this folder is served publicly at `/advisors/<file>`.
