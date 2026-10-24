# Advisor portraits: prompts for ChatGPT (or Gemini)

For the owner to generate the seven portraits (Step 8). Higgsfield had 1.64 credits on 2026-10-23: Nano Banana Pro
costs 2 credits a portrait, GPT Image 2.5 0.25, so the owner chose ChatGPT. Style source: `docs/advisors-portraits-brief.md`;
the shared style line is refined once the owner's screenshot of the reference ("Roast Room") is in.

## How to use

1. Start one ChatGPT conversation for all seven, so the style stays the same. If you have the reference
   screenshot, attach it to the first message and add: "Match the style of this image."
2. Paste **the style line**, then **one advisor line**. Ask for a square image.
3. If a face does not look like the person, attach a public photo of them and say "use this only for the face".
4. Download each as PNG and name it exactly: `buffett.png`, `lynch.png`, `dalio.png`, `marks.png`,
   `alwaleed.png`, `alrajhi.png`, `chair.png`. Send the seven files back; Claude resizes them, converts them to
   WebP and puts them on the site.

## The style line (paste first, every time)

> Friendly 3D cartoon caricature, like a character from a modern animated film: slightly exaggerated head and
> features, soft studio lighting, smooth matte surfaces. Head and shoulders, facing the viewer, centred so the
> face fits inside a circle crop. Plain solid dark graphite background (#14161B), no gradient, no glow, no text,
> no logos. Clothing in neutral tones (charcoal, navy, grey, white) with at most one small touch of orange
> (#FF6A1A). Clearly a cartoon, not a photo. Square image.

## One line per advisor

1. **Warren Buffett** (`buffett.png`): a caricature of Warren Buffett as he looks in recent public photos: white
   hair, dark-rimmed glasses, warm grandfatherly smile; navy suit, white shirt, small orange tie.
2. **Peter Lynch** (`lynch.png`): a caricature of Peter Lynch, the former Fidelity Magellan fund manager, as he
   looks in public photos: thick white hair, friendly wide smile; light grey suit, white shirt, no orange.
3. **Ray Dalio** (`dalio.png`): a caricature of Ray Dalio as he looks in recent public photos: calm, thoughtful
   expression; charcoal jacket over a dark open-collar shirt, no tie.
4. **Howard Marks** (`marks.png`): a caricature of Howard Marks, co-founder of Oaktree Capital, as he looks in
   recent public photos: gentle, wise expression; grey suit, white shirt, dark tie.
5. **Prince Alwaleed bin Talal** (`alwaleed.png`): a respectful caricature of Prince Alwaleed bin Talal as he looks
   in recent public photos: confident smile; white thobe, white ghutra with a black agal.
6. **Abdullah bin Sulaiman Al-Rajhi** (`alrajhi.png`): a respectful caricature of Abdullah bin Sulaiman Al-Rajhi,
   chairman of Al Rajhi Bank, as he looks in public photos: kind, composed expression; white thobe, white ghutra
   with a black agal, dark bisht. (If the face is not right, attach a public photo of him.)
7. **The Chair** (`chair.png`): not a person. A wooden judge's gavel resting on a round dark table, same 3D cartoon
   style and background, a small orange accent on the gavel's band.

## Notes

- Caricatures of living people: the lawyer reviews them at the end (PROJECT.md Step 7). Keep the prompts
  respectful; no endorsement, no logos of their companies.
- The site shows them small (22–66 px), so a clear face and simple shapes matter more than detail.

---

# Step 22: the same seven, cut out and speaking

Step 8's portraits are done and live. Step 22 needs two more things from the same seven characters, and
**the faces must not change** — they are approved and the lawyer reviews these at Step 7. So do not
regenerate them from the text prompts above. Attach the image you already have and ask for a change to it.

**The files to attach are in `docs/advisors-portraits/png-for-chatgpt/`** — the seven approved portraits as
1024 × 1024 PNG, ready to drag straight into ChatGPT (it often refuses WebP). The WebP originals they were
made from are beside them in `docs/advisors-portraits/originals/`. That PNG folder is not in git (it is
7.6 MB of the same pixels); if it is missing, ask Claude to make it again from the WebP originals.

## What is needed: 13 images

| For | File to send back | How many |
|---|---|---|
| Each of the six advisors, background removed | `buffett-cut.png`, `lynch-cut.png`, `dalio-cut.png`, `marks-cut.png`, `alwaleed-cut.png`, `alrajhi-cut.png` | 6 |
| Each of the six advisors, mouth open | `buffett-talk.png`, `lynch-talk.png`, `dalio-talk.png`, `marks-talk.png`, `alwaleed-talk.png`, `alrajhi-talk.png` | 6 |
| The Chair's gavel, background removed | `chair-cut.png` | 1 |

The Chair needs no mouth-open image: it is a gavel, and a seat without one simply stays still while it
writes (Step 22's default).

## Prompt 1 — background removed (seven times, one per seat)

Attach the seat's existing image, then:

> Remove the background from this image completely, so it is fully transparent (PNG with an alpha
> channel). Keep the character exactly as it is: same face, same expression, same pose, same clothing,
> same lighting and colours. Do not redraw, restyle or re-light anything. Cut cleanly around the hair,
> ears and shoulders. Export as PNG with transparency, square, at least 1024 × 1024.

## Prompt 2 — mouth open (six times, advisors only)

Attach the **same original** (not the cut-out), then:

> Same character, same face, same framing, same pose, same clothing, same lighting — change only the
> mouth: open as if speaking mid-sentence, a natural talking shape, not a wide grin or a shout. Teeth may
> show a little. Everything else in the image must be identical to the original. Background fully
> transparent (PNG with an alpha channel). Export as PNG with transparency, square, at least 1024 × 1024.

If a result changes the face, say: "The face changed. Use the attached image again and change only the
mouth." Two images that differ in anything but the mouth will flicker when they swap.

## Also needed: the reference image

The one image of **exactly how the room should look** — the second reference you mentioned on 2026-10-23.
Without it, the arc, the table and where the caption sits are guesses, and guessing means building the
look twice. Send it with the portraits.

## What Claude does with them

Resize to 512 × 512, convert to WebP under 200 KB keeping the alpha, put the cut-outs in
`web/public/advisors/` (replacing the dark-background files there — the small circles look the same,
because the disc draws its own background behind them), add the talk images as `<id>-talk.webp`, name them
in each seat file (`portrait:` and `portrait_talk:`), and keep your PNGs in
`docs/advisors-portraits/originals/`. Then the room gets its large busts, full names and mouth movement,
and goes to beta for your approval.

## Notes

- Transparency is what makes the large busts possible: a dark square behind each head would sit on top of
  the table instead of standing at it.
- The mouth swap runs about every 150 ms while that advisor's line is typing, and is off entirely for
  anyone who asks for reduced motion.

## Which tool for which half (tested 2026-10-25)

The two halves are not the same kind of job, and the same tool is wrong for both.

### The seven cut-outs: not a generative job at all

Measured on the approved portraits: the background is a single flat colour, `rgb(20,21,24)` — the brand
graphite — with a deviation of ±2 across the top corners. That means the background can be *removed*
rather than *redrawn*, and nothing about the face can change. Asking any image model to "remove the
background" risks it regenerating the portrait, which is the one thing that must not happen: these faces
are approved and the lawyer reviews them at Step 7.

Claude tried it here with a flood-fill colour key (no model, no credits). The result is
`cutout-trial-2026-10-25.png`, every cut-out over bright orange so the flaws show:

- **Good enough: Buffett, Lynch, Dalio, Marks, the Chair.** The only loss is a little chewing of wispy
  hair, and because the page behind them is the same graphite the background was, it does not show.
- **Broken: Alwaleed and Al-Rajhi.** Their black agal — and Al-Rajhi's dark bisht — are nearly the same
  colour as the background and touch it, so the key eats through them. Orange shows through the band.

That failure is exactly what a trained matting model handles and a colour threshold cannot. So:

| Tool | For the cut-outs |
|---|---|
| **A background remover** (remove.bg, Photoshop "Remove Background", Pixelmator, `rembg`) | **Best.** Built for this, including dark hair and dark garments against a dark field. One click per image, no credits, and it cannot change a face |
| Claude's colour key | Free and instant, and already good for five of the seven. Ask for it if you want those five now |
| ChatGPT / any image model | **Avoid.** It redraws rather than cuts, and a redrawn face is the thing we cannot have |

### The six mouth-open images: this half *is* generative

Here something must be invented — the same face with a different mouth — so a model is unavoidable. What
matters is character consistency: the talking frame and the closed frame must differ **only** at the
mouth, or the face will flicker twice a second when they swap.

| Tool | For the mouth-open set |
|---|---|
| **Nano Banana Pro** (Gemini 3 Pro Image, on Higgsfield) | **Best for a still.** Its strength is a targeted edit that leaves the rest of the character identical. 2 credits each, so 12 for the six — the account had 1.64 on 2026-10-23, so it needs topping up |
| **A talking-head / image-to-video model**, then take one frame | **Best fidelity, and worth considering.** It animates the actual pixels of the portrait, so identity is preserved by construction rather than by instruction. Frames are softer and usually no more than 1080p, which is ample: the room draws these at 160–200 px. More work per advisor, and the mouth shape has to be picked by eye |
| ChatGPT / GPT Image 2.5 | Cheapest (0.25 a go) and it made the originals, but it is the weakest of the three at *keeping* a face while changing one feature. If it is used, compare each result against the original before accepting it |

If the owner would rather not generate anything: the room already works without talk images. A seat with
no `portrait_talk` simply stays still while it writes, and Step 22 still gains the large busts and the
full names. Mouth movement is the part that needs the six images.
