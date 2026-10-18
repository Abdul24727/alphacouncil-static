# Advisor portraits

Caricature portraits for the advisors' debate room, supplied by the owner. Until a seat's portrait is here and named
in its file (`api/app/advisors/<id>.md`, `portrait: <file>`), the screen shows the seat's initials on a graphite disc.

- One file per seat, named after the seat id: `buffett.webp`, `lynch.webp`, `dalio.webp`, `marks.webp`, `chair.webp`.
- Square, at least 512 × 512 px, WebP or PNG, under 200 KB. Head and shoulders, centred, facing the camera.
- Background transparent or the brand graphite (#14161B). BRAND.md applies: no gradients, glows, teal or purple.
- Drawn as caricatures, so nobody mistakes a seat for the real person (the screen's disclaimer says the same).

Everything in this folder is served publicly at `/advisors/<file>`.
