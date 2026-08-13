# Wander — a web performance before/after

A comparative demo. The same editorial travel page, served two ways, so the effect of
media optimization can be measured side by side. Plain HTML and CSS, no JavaScript, no
framework, no build step — the media is the only variable.

**Live:** https://eitanp461.github.io/cloudinary-demo/

| | |
|---|---|
| [`/before/`](before/) | Unmodified original images, no optimization |
| [`/after/`](after/) | Same page, images delivered by Cloudinary |
| [`/video-before/`](video-before/) | Unmodified original 4K video, no optimization |
| [`/video-after/`](video-after/) | Same page, film delivered by Cloudinary |

## What `/after/` changes

Only the `<img>` tags. `after/assets/styles.css` is a byte-identical copy of the
`/before/` stylesheet, and the two documents are the same markup once the `<img>`
tags are collapsed — no CSS, copy, or layout changes.

Each image is delivered from Cloudinary with four transformation parameters:

| | |
|---|---|
| `f_auto` | negotiates AVIF / WebP / JPEG from the request's `Accept` header |
| `q_auto` | picks a quality per image from the image's own content |
| `c_limit` | scales down to the requested width, never up |
| `w_<n>` | one derived width per `srcset` entry |

plus `srcset`/`sizes` so the browser requests the width it will actually paint,
`loading="lazy"` on the gallery tiles, and `fetchpriority="high"` on the hero.

Aspect ratios are kept at the originals', so the CSS crops the hero exactly as it
does in `/before/`. Each tile also pins `aspect-ratio` inline: Cloudinary rounds a
resized height to a whole pixel, and without the pin that rounding shifts a
gallery column by 1px.

### Measured

Image payload for the whole page, in the widths a browser actually selects:

| Scenario | `/before/` | `/after/` | |
|---|---|---|---|
| Desktop 1440px, 1× | 31.05 MB | **646 KB** | 98.0% smaller |
| Desktop 1440px, 2× | 31.05 MB | **2.06 MB** | 93.4% smaller |
| Phone 390px, 3× | 31.05 MB | **1.70 MB** | 94.5% smaller |

Rendering was compared with full-page screenshots at three viewports. Document
height and every image box match exactly, and outside the photographs the two
renders are pixel-identical. Inside them the mean per-channel difference is about
1.7% — lossy recompression, not a visible change.

`f_auto` returns WebP for most tiles and falls back to JPEG on the largest
derivatives of the 42-megapixel hero.

## The video baseline

[`/video-before/`](video-before/) is the same exercise for video. It is a single short
film in a page built from the same stylesheet as `/before/`, with one `<video>` tag and
the camera original behind it:

| | |
|---|---|
| Source | `video-before/assets/host-at-home.mp4` |
| Dimensions | 4096 × 2160 |
| Duration | 16.4 s, 24 fps |
| Codec | H.264 High profile, ~22 Mbps, no audio track |
| Payload | **43.3 MB**, the same file at every viewport |

What makes it the *before*:

- **one rendition** — a 390px phone downloads the same 4K file as a 5K display
- **one codec** — H.264 only, so no browser is offered AV1, VP9 or HEVC
- **progressive MP4** — not HLS or DASH, so there is no adapting to a slow
  connection once the download has started
- **`preload="auto"`** — the fetch begins on load whether or not the viewer
  ever presses play
- **no poster** — the frame stays empty until enough video has arrived to paint

The player pins `aspect-ratio: 4096 / 2160` in CSS rather than relying on the file's own
dimensions, so the box is reserved before any video arrives and `/video-after/` can serve
a smaller rendition without shifting the layout.

`video-before/assets/styles.css` is `/before/`'s stylesheet plus a `.film` block and a
`.notes` prose column; nothing existing was changed.

It autoplays muted — the original has no audio track — but deliberately does **not**
loop. A looping video re-fetches the whole file every 16 seconds once the cache is out
of the picture, which makes the baseline number impossible to quote.

### Measured

One cold load in headless Chrome 151, played through to the end, counting body bytes
written by the local server rather than trusting the DevTools total:

| Viewport | Video bytes on the wire |
|---|---|
| Desktop 1440px | 45.89 MB |
| Phone 390px | 48.68 MB |

Both are *above* the 43.3 MB file, and that is not a mistake: the media element opens
several range requests and re-fetches a few MB of overlap as playback advances, so the
run-to-run figure lands a little over the file size. The number that matters is that
neither viewport gets anything smaller — there is only one rendition, so the phone pays
4K prices for a 390px-wide box.

## What `/video-after/` changes

The `<video>` tag, plus one deliberate CSS divergence for portrait phones (its own section
below). Everywhere else `video-after/assets/styles.css` matches the `/video-before/`
stylesheet, and the two documents are the same markup once the media element is collapsed —
no copy or layout changes. Behaviour is unchanged too: it still autoplays muted, still shows
controls, still does not loop.

The film is delivered from Cloudinary with three transformation parameters:

| | |
|---|---|
| `f_auto:video` | negotiates container and codec per browser — VP9/WebM for Chrome and Firefox, HEVC for Safari, where the baseline can only ever be H.264. The `:video` qualifier is required because these URLs carry no file extension; plain `f_auto` would resolve to an image |
| `q_auto` | picks a quality per video from the video's own content |
| `c_limit,w_<n>` | scales down to the requested width, never up |

Responsiveness is done with `media` on `<source>` — the video counterpart of `/after/`'s
`srcset`/`sizes`, and, like it, resolved by the browser with no JavaScript. The player box
is `calc(min(100vw, 76rem) - 3rem)`, so it tops out at 1168 CSS px; each tier asks for the
smallest rendition that still covers that box at that viewport and pixel density:

| Viewport | 1× | hi-DPI | Delivered as |
|---|---|---|---|
| portrait ≤ 30rem | `w_480` | `w_960` | 4:5, tracking crop |
| ≤ 30rem | `w_480` | `w_960` | 1.896:1, uncropped |
| ≤ 46rem | `w_720` | `w_1440` | 1.896:1 |
| ≤ 60rem | `w_960` | `w_1920` | 1.896:1 |
| wider | `w_1280` | `w_1920` | 1.896:1 |

Sources are evaluated top to bottom and the first match wins, so the tiers run narrow to
wide and the last `<source>` carries no `media` at all as the catch-all. The hi-DPI column
stops at `w_1920` instead of the 2336 a 2dppx display would imply: past roughly 1.6× density
the extra lines are not visible in 24fps motion, and they cost about twice the bytes.

A browser that does not understand `max-resolution` fails those queries rather than
misreading them and falls through to the next, coarser tier — it over-serves a little, it
never breaks.

Two things the baseline listed as missing are now present: a `poster` (frame 0 of the same
asset via `so_0`, 37 kB as WebP) so the first frame paints before any video arrives, and
`preload="metadata"` in place of `preload="auto"`, so a browser or data saver that blocks
autoplay shows the poster and a play button instead of starting an unrequested download.

`media` on `<source>` inside `<video>` is worth a note, because it is often assumed not to
work. It was verified here rather than taken on trust: both Chrome 151 and Firefox 143
pick the rendition their viewport matches, and both skip a `<source>` whose `media` can
never match — so the attribute is genuinely being evaluated, not ignored.

One limit of the technique is worth stating plainly. A browser that ignores `media` on
`<source>` takes the first source it can play, which here is the narrow portrait crop.
Chrome has honoured it since 3 and Safari since 3.1, but Firefox 53–119 honoured it only
inside `<picture>`, so those versions would show the 4:5 crop at any window size. Firefox
120 fixed that in 2023. The ladder stays ordered narrow-to-wide for everyone else.

### The film in portrait

Letterboxed into a 390px-wide phone, a 1.896:1 film is a 206px strip — about a fifth of the
screen. That is the correct rendering of the asset and a poor use of the device, so on
portrait phones `/video-after/` asks for a different frame instead of a smaller one: a 4:5
crop, with the player box taken edge to edge.

Cropping 1.896:1 to 4:5 keeps only 42% of each frame's width, and the subject does not sit
in the middle of the frame — a plain centre crop slices his face at the right edge. So the
crop is content-aware:

| | |
|---|---|
| `c_fill,g_auto` | a tracking crop. Cloudinary analyses the whole film and moves the crop window to follow the subject, easing between frames rather than cutting. `c_fill` or `c_fill_pad` is required; the resize-only modes ignore `g_auto` |

Four things about `g_auto` on video cost real time to find, and every one of them is
load-bearing here:

1. **It must sit in its own transformation component, and that component must come first.**
   `f_auto:video,q_auto,…,g_auto` in a single component is a 400 — *"g_auto must be in a
   transformation component by itself"*. Putting the delivery component first is a 500. Only
   `<crop>/<delivery>` works.
2. **A form exists that returns 200 and silently does nothing.** `f_auto:video,q_auto/g_auto/ar_4:5,c_fill,w_720`
   answers instantly with a plain centre crop — no error, no tracking, and nothing in the
   response to tell you so.
3. **Tracking crops derive asynchronously.** Cloudinary answers `423` with
   `x-cld-error: Video tracking-crop is pending` until the analysis and encode finish, so
   these renditions have to be warmed before a real visitor arrives.
4. **The first 200 after derivation can still be wrong.** It arrives at the right dimensions
   but as un-negotiated H.264. Warming means polling until the codec you asked for shows up
   — checked with `ffprobe`, not with the status line or `Content-Type`.

The portrait tier is also the one place where naming codecs beats `f_auto`. Behind a chained
crop, `f_auto` only negotiated half the way: Chrome and Firefox got VP9, but Safari — the
browser that matters most in portrait — got H.264 at 1.56 MB, even though the same crop
encodes to HEVC at 771 kB when asked directly. Five component arrangements were tried and
none restored it, so each portrait tier lists its formats and lets the browser choose by
`type`:

| Width | VP9/WebM | HEVC/MP4 | What `f_auto` handed Safari |
|---|---|---|---|
| `w_480` | 266 kB | 350 kB | 607 kB |
| `w_960` | 584 kB | 771 kB | 1,562 kB |

WebM is listed first because VP9 is the smaller of the two here for everyone who can play
it, and HEVC then catches Safari. A browser that can play neither falls through to the
landscape sources, where `f_auto` still negotiates normally; the CSS crops that wide frame
to fit, which is a worse frame than `g_auto` picks but not a broken page.

Two CSS details go with it. The player's `aspect-ratio` becomes `4 / 5` in the same media
query, and it has to stay in step with the `ar_4:5` renditions or the video would letterbox
inside its own box — the renditions arrive as exactly 480×600 and 960×1200, so it does.
And `object-fit: cover` with `object-position: 62% center` is there for the **poster**, not
the video: `poster` takes a single URL and cannot be art-directed without JavaScript, so the
wide still is the one asset that must be cropped by the browser, and 62% biases that crop
toward the subject instead of clipping him.

The treatment is scoped to `(orientation: portrait) and (max-width: 30rem)`. A portrait
tablet is wide enough that the cinematic frame still reads well, and a full-bleed 4:5 at
768px would stand 920px tall.

This costs bytes, and the honest number is worth stating: a hi-DPI portrait phone goes from
about 356 kB to about 628 kB, because the 4:5 crop at `w_960` is 584 kB where the letterboxed
`w_960` was 313 kB. It is still 98.5% below the 43.3 MB baseline. Dropping the tier to
`w_720` would claw most of that back; `w_960` was kept because it is exactly 2× the tier's
480px maximum and reuses a width the ladder already derives.

### Measured

The rendition ladder, as delivered (16.4 s, no audio track):

| Width | VP9/WebM — Chrome, Firefox | HEVC/MP4 — Safari |
|---|---|---|
| `w_480` | 131 kB | 171 kB |
| `w_720` | 238 kB | 296 kB |
| `w_960` | 313 kB | 412 kB |
| `w_1280` | 465 kB | 597 kB |
| `w_1440` | 512 kB | 671 kB |
| `w_1920` | 707 kB | 877 kB |

Whole-page media payload, from Resource Timing inside the page — poster plus the one
rendition the viewport selects, in Chrome:

| Scenario | Rendition chosen | `/video-before/` | `/video-after/` | |
|---|---|---|---|---|
| Desktop 1440px, 1× | `w_1280` | 43.3 MB | **503 kB** | 98.8% smaller |
| Desktop 1440px, 2× | `w_1920` | 43.3 MB | **744 kB** | 98.3% smaller |
| Laptop 1024px, 1× | `w_1280` | 43.3 MB | **503 kB** | 98.8% smaller |
| Tablet 800px, 2× | `w_1920` | 43.3 MB | **744 kB** | 98.3% smaller |
| Phone 390px, 3×, portrait | `ar_4:5,c_fill,g_auto,w_960` | 43.3 MB | **622 kB** | 98.6% smaller |

The phone row is the expensive one, and it is expensive by choice: the 4:5 crop costs 584 kB
where the letterboxed `w_960` cost 313 kB. That is the price of the portrait treatment above.

Counting bytes on the wire instead — one cold headless Chrome per row, autoplayed through
to the end, tallied by a counting proxy in front of the browser so the locally served
baseline and the CDN-served variant go through the same meter. Three full runs, shown as a
range where they disagreed:

| Scenario | `/video-before/` | `/video-after/` |
|---|---|---|
| Desktop 1440px, 1× | 52.9 – 59.6 MB | 0.54 MB |
| Desktop 1440px, 2× | 52.9 – 57.3 MB | 0.77 – 0.79 MB |
| Laptop 1024px, 1× | 52.2 – 59.8 MB | 0.53 – 0.54 MB |
| Phone 390px, 3× | 52.7 – 59.2 MB | 0.59 MB |

Note which column is stable. `/video-after/` repeats to within a couple of kB, while the
baseline swings by about 7 MB between identical runs: a progressive 43 MB file is fetched
by however many overlapping range requests the media element happens to open that time,
and each retry re-downloads bytes the browser already had. Neither column lines up exactly
with the payload table — the baseline reads well above it for the reason just given, and the
phone row reads slightly below its 622 kB payload because this harness measures a top-level
page that does not always fetch the poster the payload harness recorded. Which is why the
payload table is the fairer comparison; the direction is not in question at either level of
measurement.

Rendering was compared by measuring, at five viewports, the bounding box of every
structural element on both pages plus total document height. On every landscape viewport all
17 boxes match exactly, because the CSS pins `aspect-ratio: 4096 / 2160` on the player rather
than letting the delivered file's own dimensions size it — Cloudinary rounds a resized height
to a whole pixel (`w_1280` arrives as 1280×674, not 1280×674.9), and the pin absorbs that.

Portrait phones are where the two pages are meant to differ, so they were measured against a
different standard: the film should grow, everything else should only move down by however
much the film grew.

| Portrait viewport | Film height | Share of screen | Rendition selected |
|---|---|---|---|
| 360×800 @3× | 165 → 450 px | 20.6% → 56.2% | `ar_4:5,c_fill,g_auto,w_960` |
| 390×844 @3× | 180 → 488 px | 21.4% → 57.8% | `ar_4:5,c_fill,g_auto,w_960` |
| 412×915 @3× | 192 → 515 px | 21.0% → 56.3% | `ar_4:5,c_fill,g_auto,w_960` |
| 430×932 @3× | 201 → 538 px | 21.6% → 57.7% | `ar_4:5,c_fill,g_auto,w_960` |
| 480×854 @2× | 228 → 600 px | 26.7% → 70.3% | `ar_4:5,c_fill,g_auto,w_960` |

So the film ends up 2.6–2.7× taller and occupies a little under 60% of a typical phone
screen instead of a little over 20%. Every other element keeps its x, width and height and
shifts down by exactly the film's height increase — checked numerically, per element, not by
eye. iPad portrait (768×1024) and desktop (1440×900) are unaffected: 15/15 boxes identical,
film height unchanged, still on the uncropped `c_limit` ladder.

The delivered ratio was checked against the CSS box ratio at every viewport and matches to
0.00%. That check matters more than it looks: with `object-fit: cover` in play a mismatch
would no longer show up as visible bars, it would silently crop the frame a second time.

Two things were verified by looking at frames rather than numbers. Extracting frames at
matching timestamps showed that a centre crop does slice the subject's face while `g_auto`
frames him fully, with the crop window visibly moving between frames — so the tracking is
real and not a static offset. The same comparison between the VP9 and HEVC encodes of the
`w_960` crop shows identical framing at every timestamp, confirming the two formats share one
set of crop decisions.

Safari was the one gap in this: WebKit could not be driven headlessly here, so its behaviour
is established from `curl` probes carrying Safari user agents and from the codec of the bytes
that came back, not from a running browser.

## Running locally

```sh
python3 serve.py 8000
```

Then open http://localhost:8000 with DevTools open and *Disable cache* ticked.

`python3 -m http.server` is fine for the image pages but not for `/video-before/`: it
ignores the `Range` header and answers with the whole file and a `200`, so the scrub bar
does nothing and the player can sit waiting on 43 MB it never asked for in one piece.
`serve.py` is the same standard-library server with `206 Partial Content` support added —
no dependencies, still no build step.

## The Cloudinary clouds

Each optimized variant points at its own cloud, both provisioned with
[`npx @cloudinary/cloud`](https://www.npmjs.com/package/@cloudinary/cloud):

| | | |
|---|---|---|
| `/after/` | `ka8stfl5` | provisioned 2026-08-11, still delivering |
| `/video-after/` | `zosttxi5` | claimed |

`.env` holds the API secrets and is gitignored — keep it that way.

`npx @cloudinary/cloud` hands out disposable clouds: they expire unless claimed through the
claim URL in `.env`, and while unclaimed **delivery is allow-listed to the IP addresses
given at provisioning time** — the URLs return `401` from anywhere else, including from a
different network on the same machine. That matters for a site published to GitHub Pages,
where every visitor arrives from an address that was never on the list, so the cloud behind
`/video-after/` was claimed before publishing.

That allow-list is enforced per address family, which is worth knowing before debugging it:
a list containing only an IPv4 address answers real browser traffic with `401 ACL deny`,
because browsers prefer IPv6 where it is available. Both addresses have to be passed:

```sh
npx @cloudinary/cloud --ip <your-v4> --ip <your-v6>
```

To repoint either variant at a different cloud, replace the cloud name in its
`index.html` — the transformation strings are otherwise portable.

## Credits

All photographs are from the free Unsplash library under the
[Unsplash License](https://unsplash.com/license); no Unsplash+ images are used. The film
is from the free Pexels library under the [Pexels License](https://www.pexels.com/license/).
Photographers, the videographer, and per-file source URLs are in [CREDITS.md](CREDITS.md).
