# Repo file lists for individual game imports

Add one file per repository named:

`<owner>__<repo>.txt`

Example:

`Neruvy__web-port.txt`

Each line should be a playable HTML path from that repo, for example:

```
games/1v1-lol/index.html
projects/slope/index.html
```

When present, `scripts/fetch_games.py` will import each line as an individual game entry with iframe URL candidates.
