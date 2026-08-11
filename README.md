# Wander — a web performance before/after

A comparative demo. The same editorial travel page, served two ways, so the effect of
image optimization can be measured side by side. Plain HTML and CSS, no JavaScript, no
framework, no build step — images are the only variable.

**Live:** https://eitanp461.github.io/cloudinary-demo/

| | |
|---|---|
| [`/before/`](before/) | Unmodified originals, no optimization |
| `/after/` | Not built yet |

## Running locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000 with DevTools open and *Disable cache* ticked.

## Credits

All photographs are from the free Unsplash library under the
[Unsplash License](https://unsplash.com/license); no Unsplash+ images are used.
Photographers and per-image source URLs are in [CREDITS.md](CREDITS.md).
