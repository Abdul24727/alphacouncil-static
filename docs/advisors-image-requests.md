# Advisor images: one request per image

A worklist for Step 22. Each block below is **self-contained**: open a fresh chat, attach the one file it
names, paste the block, save the result. Nothing refers to an earlier message, so the order does not
matter and no chat needs to know about any other.

**One chat per image is fine here** — and it is worth knowing why, because the Step 8 brief said the
opposite. There, seven portraits were being invented from text, so they had to share a conversation or
they would not have shared a style. Here every request **attaches the finished portrait** and asks for one
change to it. The consistency comes from the attachment, not from the chat's memory.

**The files to attach** are in `docs/advisors-portraits/png-for-chatgpt/` (1024 × 1024 PNG). If that
folder is missing, ask Claude to make it again from `docs/advisors-portraits/originals/`.

**The rule that matters in every one of these:** the face must not change. These portraits are approved,
they are live on the site, and the lawyer reviews them at Step 7. If a result comes back with a different
face, do not keep it — reply "The face changed. Use the attached image again and change only the mouth,"
or start the chat again.

---

# Part A — the six mouth-open images

The generative half. Each gives the room a second frame per advisor, swapped with the first about every
150 ms while that advisor is writing, so the mouth appears to move. **The two frames must differ only at
the mouth.** Anything else that changes — a shifted glasses frame, a different hair strand, a slightly
turned head — will read as a flicker rather than as speech.

Optional: skip Part A entirely and the room still gets its large busts and full names; the seats just do
not move their mouths.

## A1 · Warren Buffett

Attach `buffett.png`, then paste:

> This is a 3D cartoon caricature portrait. Change **only the mouth**: open it as if he is speaking
> mid-sentence — a natural talking shape, not a grin and not a shout. Teeth may show a little.
> Everything else must be pixel-for-pixel the same: the same face and age lines, the same white hair,
> the same dark-rimmed glasses in the same position, the same navy suit, white shirt and orange tie, the
> same lighting and the same head angle. Do not restyle, re-light, re-crop or redraw anything else.
> Give the image a fully transparent background (PNG with an alpha channel), square, 1024 × 1024.

Save as `buffett-talk.png`. Check: glasses and tie identical, only the mouth differs.

## A2 · Peter Lynch — **read this one first, he is the odd one out**

His approved portrait is **already a wide open-mouth smile with teeth showing**. A plain "open the mouth"
request would come back looking almost the same, and the swap would show no movement at all. So ask for a
clearly *different* open shape, and keep his existing grin as the resting frame.

Attach `lynch.png`, then paste:

> This is a 3D cartoon caricature portrait of a smiling man whose mouth is already open in a wide grin.
> Change **only the mouth** into a clearly different shape: rounded and open as if he is mid-word on an
> "oh" sound, rather than smiling. It must be obviously different from the grin in the attached image.
> Everything else must be pixel-for-pixel the same: the same face and age lines, the same thick white
> hair, the same thin silver glasses in the same position, the same light grey suit and white shirt, the
> same lighting and the same head angle. Do not restyle, re-light, re-crop or redraw anything else.
> Give the image a fully transparent background (PNG with an alpha channel), square, 1024 × 1024.

Save as `lynch-talk.png`. Check: put it beside the original — the mouths must look clearly different, or
his seat will look frozen.

## A3 · Ray Dalio

Attach `dalio.png`, then paste:

> This is a 3D cartoon caricature portrait. Change **only the mouth**: open it as if he is speaking
> mid-sentence — a natural talking shape, not a grin and not a shout. Teeth may show a little.
> Everything else must be pixel-for-pixel the same: the same face and age lines, the same grey hair, **no
> glasses**, the same charcoal jacket over a dark open-collar shirt with no tie, the same lighting and the
> same head angle. Do not restyle, re-light, re-crop or redraw anything else.
> Give the image a fully transparent background (PNG with an alpha channel), square, 1024 × 1024.

Save as `dalio-talk.png`. Check: still no glasses and no tie.

## A4 · Howard Marks

Attach `marks.png`, then paste:

> This is a 3D cartoon caricature portrait. Change **only the mouth**: open it as if he is speaking
> mid-sentence — a natural talking shape, not a grin and not a shout. Teeth may show a little.
> Everything else must be pixel-for-pixel the same: the same face and age lines, the same hair, the same
> round glasses in the same position, the same grey suit, white shirt and dark tie, the same lighting and
> the same head angle. Do not restyle, re-light, re-crop or redraw anything else.
> Give the image a fully transparent background (PNG with an alpha channel), square, 1024 × 1024.

Save as `marks-talk.png`. Check: glasses and tie identical.

## A5 · Prince Alwaleed bin Talal

Attach `alwaleed.png`, then paste:

> This is a respectful 3D cartoon caricature portrait. Change **only the mouth**: open it as if he is
> speaking mid-sentence — a natural talking shape, not a grin and not a shout. The moustache above it
> must keep its exact shape. Everything else must be pixel-for-pixel the same: the same face, the same
> tinted glasses in the same position, the same white ghutra, the same **solid black agal** on top of it,
> the same white thobe, the same lighting and the same head angle. Do not restyle, re-light, re-crop or
> redraw anything else.
> Give the image a fully transparent background (PNG with an alpha channel), square, 1024 × 1024.

Save as `alwaleed-talk.png`. Check: the moustache is unchanged and the agal is still solid black.

## A6 · Abdullah bin Sulaiman Al-Rajhi

Attach `alrajhi.png`, then paste:

> This is a respectful 3D cartoon caricature portrait. Change **only the mouth**: open it as if he is
> speaking mid-sentence — a natural talking shape, not a grin and not a shout. Everything else must be
> pixel-for-pixel the same: the same face, the same white ghutra, the same **solid black agal** on top of
> it, the same white thobe and the same dark bisht with its gold trim, the same lighting and the same head
> angle. Do not restyle, re-light, re-crop or redraw anything else.
> Give the image a fully transparent background (PNG with an alpha channel), square, 1024 × 1024.

Save as `alrajhi-talk.png`. Check: the agal is solid black and the bisht's gold trim is unchanged.

**The Chair needs nothing here.** It is a gavel, and a seat with no talking frame simply stays still while
it writes.

---

# Part B — the seven cut-outs, only as a fallback

**Normally skip this part.** The decision on 2026-10-25 is to run all seven through a background remover,
which cannot alter a face and handles the black agal that a colour key could not. Use Part B only if the
remover gives a poor result on a particular seat.

If you do use it, attach that seat's file from `png-for-chatgpt/` and paste:

> Remove the background from this image completely so it is fully transparent (PNG with an alpha channel).
> Keep the character exactly as it is: the same face, expression, pose, clothing, lighting and colours. Do
> not redraw, restyle, re-light or re-crop anything — this is a cut-out, not a new picture. Cut cleanly
> around the hair, the ears and the shoulders. Export as PNG with transparency, square, 1024 × 1024.

Save as `<id>-cut.png`. Then check the face against the original before keeping it: a model asked to cut
out will sometimes redraw instead, and a redrawn face is the one outcome that must not reach the site.

---

# The worklist

| # | Image | File to attach | Save as | Done |
|---|---|---|---|---|
| A1 | Buffett, mouth open | `buffett.png` | `buffett-talk.png` | ☐ |
| A2 | Lynch, **different** open shape | `lynch.png` | `lynch-talk.png` | ☐ |
| A3 | Dalio, mouth open | `dalio.png` | `dalio-talk.png` | ☐ |
| A4 | Marks, mouth open | `marks.png` | `marks-talk.png` | ☐ |
| A5 | Alwaleed, mouth open | `alwaleed.png` | `alwaleed-talk.png` | ☐ |
| A6 | Al-Rajhi, mouth open | `alrajhi.png` | `alrajhi-talk.png` | ☐ |
| B | Seven cut-outs | — | background remover, not a chat | ☐ |
| — | The reference image of the room | — | still outstanding | ☐ |

Send back whatever is done; the room can be built from the cut-outs and the reference alone, and the talk
images can arrive later without rebuilding anything.
