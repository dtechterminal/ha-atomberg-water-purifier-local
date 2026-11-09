# Dashboard card development

The card's source lives in [`frontend/`](../frontend). The integration serves the built file,
`custom_components/atomberg_purifier_local/www/atomberg-purifier-card.js`, which is committed so
HACS and manual installs need no build step.

| Path | Contents |
| --- | --- |
| `frontend/src/` | Card source: `card.js` (card and editor), `model.js` (entity discovery and formatting), `styles.js`, `art.js` (the original vector purifier illustration) |
| `frontend/build.mjs` | esbuild configuration: bundles `src/card.js` into one minified ES2021 module and writes it to `www/` |
| `frontend/tests/` | Unit tests (Node test runner + happy-dom) and browser tests (Playwright) |
| `frontend/demo/` | Interactive preview with synthetic readings; it loads the built file from `www/` |

## Rebuild the card

Requires Node.js 22.

```sh
cd frontend
npm ci
npm run build
```

The build is reproducible: with the locked dependencies it produces the committed file byte for
byte. CI rebuilds it on every push and fails if `www/atomberg-purifier-card.js` differs from the
source.

## Test and preview

```sh
npm test
npx playwright install chromium
npm run test:browser
npm run dev
```

`npm run dev` serves the repository root; open `http://127.0.0.1:8766/frontend/demo/`. The preview
uses synthetic readings and never calls a real purifier. Tests cover device selection, renamed
entities, each service type, failed commands, unavailable devices, filter estimates, read
timestamps, visual editing and mobile layouts.

The card uses Home Assistant's [custom card API](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/).
It has no runtime dependencies, CDN requests, remote fonts or app assets.
