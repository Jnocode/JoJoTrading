# Plan: JoJoTrading GitHub Pages Static Demo

## Goal
Create a recruiter-friendly public demo page for JoJoTrading at GitHub Pages, showing backtest summary, equity curve, order table, architecture, and links to GitHub/Cake.

## Scope
- Add `docs/index.html` as a static single-page demo.
- Use no external build step; pure HTML/CSS/JS with SVG/canvas-like CSS chart.
- Avoid secrets, broker credentials, or live trading claims.
- Update README with demo link.
- Push changes to main.
- Enable GitHub Pages from `/docs` on `main` if not already enabled.
- Verify the page URL after deployment starts.

## Evidence
- Save local validation output to `artifacts/logs/jojo_pages_demo_validation.log`.
- Verify files contain expected titles/links before commit.

Generates Artifact: Screenshot-equivalent public HTML demo page.
