# Ingestion pipeline

Run the catalog build with:

```bash
python -m scripts.ingest.pipeline
```

The pipeline reads all configured adapters, normalizes each record into a common
`GameEntry` shape, de-duplicates entries by `(canonical_url, title_hash)`, and
writes merged output to `data/games/catalog.json`.

When a source cannot be fetched, the error is preserved under `source_errors`
for manual follow-up.
