# Geert Greydanus archive

The research timeline of Geert Greydanus (1899–1965), published with GitHub Pages, and copies of the sources it cites.

## Source of truth

- **The HTML is the source of truth.** That means `index.html`, plus what `tools/page.py` inserts into it: the sections in `tools/sections/` and the map built from `tools/map/stops.json`. Edit these.
- **The old Claude Doc is retired.** Do not copy content from it or from an export of it; this repository supersedes it.

## Keep the PDF in step

`geert-greydanus-timeline.pdf` is printed from `index.html` and must always match it. After any change to the page, run the steps that apply, in this order:

1. If you changed `tools/map/stops.json` or `tools/map/build_map.mjs`, run `cd tools/map && npm install && npm run build`.
2. Always run `tools/build_pdf.sh`. It runs `tools/page.py` first, which re-inserts `tools/sections/` and stamps "Last updated" under the title with the current UTC time, then prints the PDF.

Commit the PDF in the same commit as the change. Never edit the PDF by hand, and never replace it with a PDF exported from anywhere else.

Every PR must carry a fresh "Last updated" stamp and a rebuilt PDF, so readers can tell whether their copy is current. Run `tools/build_pdf.sh` as the last step before the final push.

## Writing

- **State the facts as they are now known.** When a check settles a question, rewrite the text as the fact.
- **Leave out research history.** That includes dated follow-ups, "done" or "answered" notes, "last updated" lines in the text and earlier readings set beside corrected ones. (The single generated stamp under the title is the exception.)
- **Show genuine disagreement.** Where sources still disagree, give each version with its source.
- **Cite every claim.** Link to the local copy in `drive/`, `sources/` or `web/` when one exists.

## Publishing

`.github/workflows/pages.yml` deploys to GitHub Pages on every push to `main`. A deploy sometimes stalls at "syncing files" and times out after 10 minutes. If it does, re-run it from Actions → Publish site → Run workflow.
