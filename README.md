# Wander — a web performance before/after

A small editorial travel site used to demonstrate image optimization. Plain HTML and CSS,
no JavaScript, no framework, no build step — so images are the only variable.

**Live:** https://eitanp461.github.io/cloudinary-demo/

| | |
|---|---|
| [`/before/`](before/) | 7 unmodified Unsplash originals, 31.05 MiB of JPEG |
| `/after/` | not built yet |

## The baseline

`/before/` is deliberately unoptimized. The markup is ordinary — semantic `<figure>`
elements, explicit `width`/`height` on every image, a responsive two-column masonry — so
layout shift is not the story. The problem is entirely the asset pipeline: one fixed URL
per image, pointing at a camera original, eagerly loaded, JPEG only, no CDN.

| file | photographer | dimensions | size |
|---|---|---|---|
| `hero-yosemite-valley.jpg` | Aniket Deole | 7952 × 5304 | 8.56 MiB |
| `mountain-lake-braies.jpg` | Pietro De Grandi | 3966 × 5949 | 6.30 MiB |
| `coastal-road.jpg` | James Langley | 4008 × 6008 | 5.20 MiB |
| `seashore-aerial.jpg` | Shifaaz shamoon | 3070 × 5464 | 3.26 MiB |
| `ocean-waves.jpg` | Silas Baisch | 4957 × 3305 | 3.15 MiB |
| `forest-aerial.jpg` | Filip Zrnzević | 3840 × 5760 | 2.66 MiB |
| `city-skyline.jpg` | Pedro Lastra | 3465 × 2131 | 1.92 MiB |

Every image is 2.7–4.4× wider than its layout slot needs at 2× DPR, so 86–95% of the
decoded pixels are discarded. Three images totalling 16.78 MiB sit above the fold at any
viewport height from 600 px up, which is 54% of the payload.

Images account for 99.97% of the page: HTML is 4.2 KB, CSS is 4.9 KB, JavaScript is 0 B.
The page makes no requests to external domains.

GitHub Pages gzips the HTML and CSS but not the JPEGs — already-compressed image data
does not shrink, so the 31 MiB crosses the wire intact.

## Running locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000. Load `/before/` with DevTools open and *Disable cache*
ticked — on a warm cache the JPEGs come from memory and the page looks deceptively fast.

## Credits

All photographs are from the free Unsplash library under the
[Unsplash License](https://unsplash.com/license); no Unsplash+ images are used. Per-image
source URLs and photographer names are in [CREDITS.md](CREDITS.md).
