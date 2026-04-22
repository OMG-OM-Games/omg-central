# omg-central

Base scaffold for an OMG game catalog split between:

- `apps/web/`: React + Vite front-end.
- `data/`: normalized game metadata JSON and schema.

## Run web app

```bash
cd apps/web
npm install
npm run dev
```

The app loads all game files from `data/games/*.json` and renders a virtualized catalog list with fuzzy search and filter controls.
