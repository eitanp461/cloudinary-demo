# Wander — a web performance before/after

A comparative demo. The same editorial travel page, served two ways, so the effect of
image optimization can be measured side by side. Plain HTML and CSS, no JavaScript, no
framework, no build step — images are the only variable.

**Live:** https://eitanp461.github.io/cloudinary-demo/

| | |
|---|---|
| [`/before/`](before/) | Unmodified originals, no optimization |
| [`/after/`](after/) | Same page, images delivered by Cloudinary |

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

## Running locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000 with DevTools open and *Disable cache* ticked.

## The Cloudinary cloud behind `/after/`

`/after/` points at cloud `ka8stfl5`, provisioned with
[`npx @cloudinary/cloud`](https://www.npmjs.com/package/@cloudinary/cloud).

`.env` holds the API secret and is gitignored — keep it that way.

To repoint `/after/` at a different cloud, replace the cloud name in
`after/index.html`; the transformation strings are otherwise portable.

## Credits

All photographs are from the free Unsplash library under the
[Unsplash License](https://unsplash.com/license); no Unsplash+ images are used.
Photographers and per-image source URLs are in [CREDITS.md](CREDITS.md).
