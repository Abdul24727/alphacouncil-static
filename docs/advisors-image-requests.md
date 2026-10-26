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

---

# How each one gets checked when it arrives

Send them however suits — attached here one at a time is fine. Each is checked with
`web/scripts/check-advisor-images.mjs` before it goes anywhere near the site:

```
cd web && node scripts/check-advisor-images.mjs ../docs/advisors-portraits/incoming
```

It reads `<id>-cut.png` and `<id>-talk.png`, compares each against the approved portrait in
`docs/advisors-portraits/originals/`, and reports:

- square, at least 512 px, and a real alpha channel;
- the background is actually gone (not a white or black one baked in), and the middle of the image is
  still opaque;
- **what changed against the original, and where.** The candidate is composited onto the original's own
  background colour first, so the transparency it gained is not counted as a change.

For a talk image that is the whole point: the change must be small, central, and below the eyes. A face
that has drifted shows up as a large change spanning the frame. Tested on fixtures before any real image
arrived — a mouth-sized edit reports 1.4% changed within x 41–59%, y 63–73% and passes; an image nudged a
few pixels reports 51.5% changed across the whole frame and fails four ways.

For a cut-out the bar is different: **nothing** about the subject should differ, only the background, so
anything above about 6% means it was redrawn rather than cut.

A FAIL is not necessarily a reject — a wide grin legitimately changes more pixels than a small "oh". It
is a reason to look at the two side by side before accepting.

---

# Correction, 2026-10-26: a cut-out is not a generation

**Second correction, same day — the first version of this section overstated the problem.** Cropped to
the head and scaled to match, the submitted Buffett and the approved one are the same character in the
same style: same glasses, same smile, same treatment. The only real difference in the face is a higher
hairline. The 53.9% figure was driven almost entirely by the **reframing** — the new one is pulled back
to show the chest — not by the likeness changing. So the issue is not that it looks wrong. It does not.
The issue is consistency, set out under "What the issue actually is" at the end of this section.

The first submitted `buffett-cut.png` was a **new drawing**, not the approved portrait with its
background removed: 53.9% of pixels differed across the whole frame, the framing had pulled back to show
the chest, the solid orange tie had become a polka-dot one, the glasses had changed shape, and the file
was 1254 px rather than 1024. It is a good image; it is just not a cut-out.

That is not a wording problem. Asked for a cut-out, an image generator draws a new picture that looks
like the description — it has no way to return the original pixels. So the fix is to stop it generating:

## If you want to stay in ChatGPT, ask it for code, not a picture

> Do not generate or draw anything. Use Python — PIL, or rembg if it is available — to remove the
> background from the file I attached, and give me back that exact file as a PNG with an alpha channel.
> Every pixel of the subject must be byte-for-byte the one I uploaded; the only change is that the
> background becomes transparent. Do not re-crop, resize or restyle it.

That runs in its code tool rather than its image model, so the subject cannot drift, and the question of
drawing a real person does not arise at all — nothing is being drawn.

## Or use a background remover, which cannot do anything else

No install needed, any of these: **Photopea** (free, in the browser, Image → Remove Background),
**PowerPoint** (Picture Format → Remove Background), **Canva**, **remove.bg**. Windows 11's Paint has it
too. Feed them the files in `docs/advisors-portraits/png-for-chatgpt/`.

## Either way, the bar is the same

`node scripts/check-advisor-images.mjs ../docs/advisors-portraits/incoming` must report **under about 6%
changed** for a cut-out. Above that it is a redraw, whatever it looks like.

## What the issue actually is

Not the likeness, and not the quality. Two things, both about the set rather than the picture:

1. **Framing has to match across all seven.** The live portraits are tight head crops, made for 52–66 px
   circles. The submitted one is pulled back to the chest. In an arc of busts round a table, one advisor
   framed differently reads as standing further away than the rest. Mixing the two is the thing that
   looks broken — either of them used consistently is fine.
2. **Regeneration drifts, and separate chats drift independently.** Buffett's hairline moved between
   these two. Across seven chats it will move in seven different directions, which is exactly why the
   Step 8 brief insisted on one conversation for the whole set.

And note what this means for the check: the ~6% bar in `check-advisor-images.mjs` is the right test for
**cut-outs of these exact files**. If the decision is to regenerate instead, that test does not apply and
is not a verdict on the art — what matters then is that the seven match each other.

**If the new look is preferred**, which is reasonable since its framing suits the busts better than the
live crops do: do all seven in one chat, and state the framing explicitly — "head and shoulders to
mid-chest, the head about 55% of the image height, same distance for every one of the seven."

---

# Part C — the decided route (2026-10-26): one chat, all seven, pulled back

**This supersedes Part B, and Part A waits for it.** The owner chose to adopt the new look rather than
cut out the live portraits. Parts A and B above are kept for the record; the mouth-open images in Part A
must be made from the **new** portraits once this set is settled, not from the ones now live.

The Buffett already produced is the anchor. It is in the target framing, so the other six are matched to
it rather than described from scratch — that is the whole trick for keeping seven images consistent.

## Before you start

- **One chat for all seven.** Not seven chats. Style and framing hold because every image is made in
  sight of the same reference; separate chats drift independently, which is what went wrong before.
- Have ready: the Buffett you made (the pulled-back, transparent one), and the six approved portraits
  from `docs/advisors-portraits/png-for-chatgpt/` — `lynch.png`, `dalio.png`, `marks.png`,
  `alwaleed.png`, `alrajhi.png`, `chair.png`.
- Do them in order. If one comes back off-framing, fix it before moving on, or the drift compounds.

## Message 1 — set the reference

Attach **the new Buffett**, then:

> This image is the reference for a set of seven portraits. Every one must match it exactly in style,
> framing and lighting: the same 3D cartoon caricature style, head and shoulders down to mid-chest, the
> head about 55% of the image height, the same camera distance and the same straight-on angle, soft
> studio lighting, and a fully transparent background (PNG with an alpha channel), square.
> I will send you one person at a time. For each, keep their own face, hair and clothing exactly as in
> the photo I attach — only the style, framing and background should match this reference.
> Do not change anything about this Buffett image; it is already done.

## Messages 2–7 — one advisor each, same chat

Each time, attach that advisor's approved portrait and send one line:

| Order | Attach | Say |
|---|---|---|
| 2 | `lynch.png` | Same style and framing as the reference. Keep this man's own face, thick white hair, thin silver glasses, light grey suit and white shirt. |
| 3 | `dalio.png` | Same style and framing as the reference. Keep this man's own face and grey hair, **no glasses**, charcoal jacket over a dark open-collar shirt, **no tie**. |
| 4 | `marks.png` | Same style and framing as the reference. Keep this man's own face, round glasses, grey suit, white shirt and dark tie. |
| 5 | `alwaleed.png` | Same style and framing as the reference. Keep this man's own face, moustache and tinted glasses, white thobe, white ghutra and a **solid black agal**. |
| 6 | `alrajhi.png` | Same style and framing as the reference. Keep this man's own face, white thobe, white ghutra, **solid black agal**, and the dark bisht with its gold trim. |
| 7 | `chair.png` | Same style, lighting and background as the reference, but this one is **not a person**: a wooden judge's gavel resting on its round block, filling about the same share of the frame as a head and shoulders do, with a small orange band on the gavel. |

Save them as `buffett.png`, `lynch.png`, `dalio.png`, `marks.png`, `alwaleed.png`, `alrajhi.png`,
`chair.png` — plain names, no `-cut` suffix, since these are the portraits themselves now.

## What gets checked when they arrive

Not the 6% cut-out bar — that tested cut-outs of the old files and does not apply here. Instead:

```
cd web && node scripts/check-advisor-images.mjs --set ../docs/advisors-portraits/incoming
```

which reads the alpha of each and reports where the subject sits in its frame — how tall it is, where
its top edge is, how far off centre — so a portrait shot closer or further than the rest shows up as a
number rather than being noticed later on the stage. Plus the basics: square, at least 512 px, real
transparency, opaque in the middle.

## After they are in

The new set replaces `web/public/advisors/*.webp`, which means the live site's portraits change: Step 8's
approval and screenshots are superseded and it needs its own release through beta. The lawyer's question
(d) then covers the new art. The six mouth-open images from Part A come after that, made from these.

---

## Review of the first six (2026-10-26)

**The anchor worked.** Framing is consistent across all six: subjects start between 1% and 4% of frame
height and fill 96–99%, centred at 50–51% — a spread of 2 points. All are 1254 px square with real
transparency and opaque centres. That was the thing most likely to go wrong, and it did not.

**What slipped was fidelity to each person.** The model drifted toward its own defaults rather than the
attached photos — everyone acquired a navy suit, and both Saudi advisors a red-and-white checked
shemagh. The short per-advisor lines lost to the reference image's pull.

| Seat | Against the approved portrait | Verdict |
|---|---|---|
| Buffett | the anchor, unchanged | keep |
| Dalio | no glasses and no tie, as asked; the open-collar shirt went from dark to pale | keep |
| Marks | round glasses kept; grey suit became navy, dark tie became navy with orange squares | keep |
| Lynch | **lost his wide open grin**, which was his likeness; light grey suit became navy | owner's call |
| Alwaleed | **white ghutra became a red-and-white checked shemagh** | redo |
| Al-Rajhi | **red shemagh instead of white; a full beard added where he is clean-shaven; the dark bisht with gold trim gone entirely** | redo |
| Chair | not produced | still needed |

The suit homogenisation is arguably a gain: a set in matching navy reads better round one table than a
mix of greys, and BRAND.md asks for neutral tones. The headwear and the beard are not — they are wrong
about the person.

### The two to send again, in the same chat

Attach the approved photo again each time.

**Al-Rajhi:**

> This is wrong in three ways against the photo I attached. Use that photo again and fix all three:
> (1) the headdress must be a plain **white** ghutra, not a red-and-white checked one; (2) he is
> **clean-shaven** — remove the beard completely; (3) he wears a **dark bisht with wide gold trim**
> over the shoulders, which is missing — put it back. Keep the same style, framing, lighting and
> transparent background as the reference.

**Alwaleed:**

> The headdress must be a plain **white** ghutra, not a red-and-white checked one. Everything else
> about him stays exactly as you have it. Use the attached photo again, and keep the same style,
> framing, lighting and transparent background as the reference.

**And the Chair is still to come** — the gavel, per message 7 of Part C.

### Where the set stands (2026-10-26, evening)

Six of seven in `docs/advisors-portraits/incoming/`, and they hold together: subjects start between 1%
and 4% of frame height and fill 96–99%, centred at 50–51% — spreads of 3, 2 and 1 points.

| Seat | State |
|---|---|
| buffett, dalio, marks | good |
| lynch | good; lost the wide grin, owner's call |
| alwaleed | **fixed** — white ghutra and black agal as in the approved portrait. One small drift left: the approved has tinted lenses, this has clear ones. Still plainly him; a third pass is probably not worth it |
| alrumayyan | good — and the seat swap is done in code (`api/app/advisors/alrumayyan.md`) |
| chair | **still to come** — the gavel, message 7 of Part C |

`check-advisor-images.mjs` knows the new roster: its seat list is `alrumayyan`, not `alrajhi`.

Still outstanding besides the Chair: **the reference image of how the room should look**, without which
Step 22's arc, table and caption placement are guesses.
