# OpAMP Server UI

React management UI for the OpAMP server.

## Development

```bash
npm install
npm run dev         # Vite HMR dev server on :5173 (proxies /api and /v1 to :8000)
```

## Building

```bash
npm run build       # TypeScript compile + Vite production build -> dist/
npm run type-check  # TypeScript type check only (no emit)
```

## Testing

```bash
npm run test              # Vitest watch mode
npm run test -- --run     # Single run (CI)
npm run test:coverage     # Coverage report
```

## Docker

Build and run the container:

```bash
# From repo root
docker build -f ui/Dockerfile -t opamp-ui:local ui/

# Standalone test (SPA serving only -- /api proxy requires Docker Compose)
docker run -p 8080:80 opamp-ui:local
```

The container proxies `/api/*` and `/v1/opamp` to a service named `api` on port 8000.
In standalone mode, these proxy routes will return 502 -- this is expected.
Use the Docker Compose setup (Phase 5) to run the full stack.

## Font Files

Roboto variable font files are committed in `public/fonts/` and included in the Docker build.
Source: `~/Downloads/Roboto/` -- copy `Roboto-VariableFont_wdth,wght.ttf` and the italic variant
if re-cloning without the committed files.
