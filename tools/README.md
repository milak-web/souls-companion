# Guide checks and source maintenance

The committed JSON catalogs are the app's editable data. Every imported record carries a source URL where available. Raw cached reference HTML in `audit/` is ignored by Git.

Version 2.3 adds the DS2 wiki collection, extraction and curation pipeline. Run `research_ds2_wiki.py`, then `enrich_ds2_wiki.py --apply`, then `curate_ds2_references.py`, each with `--cache <research-cache>` from the project directory. Curated corrections must run after an import; do not publish a raw import alone. `sync_ds2_roster.py` resolves the wiki's alternate enemy names; review its proposed mappings before recollecting sources. `verify_ds2_research.py` checks the known parsing failures and encounter distinctions, while `verify_reference_ui.cjs` checks local source links, merchant stock, NPC roles and actual detail-element bounds at four screen widths. `write_ds2_research_audit.py --cache <research-cache>` regenerates [the coverage report](../docs/DS2_REFERENCE_REVIEW.md). These new checks run from the project directory.

Run from `C:/Users/MK2/Desktop/PRO` while the guide server is on port 8765:

- `node DarkSouls-Guide/tools/verify.cjs`: render every catalog entry and validate generated internal destinations.
- `node DarkSouls-Guide/tools/verify_interactions.cjs`: click navigation, Back, refresh, favorites, search and legacy routes.
- `node DarkSouls-Guide/tools/verify_local_only.cjs`: render every main and supplemental entry, validate internal links and check for external requests and content-security errors. The large structural sweep serves real assets from disk to avoid flooding the development server.
- `node DarkSouls-Guide/tools/verify_details.cjs`: elemental calculations, soul trades, projectiles, armor facts, area bonfires and mobile layout.

Run `python tools/audit_catalogs.py` from the guide directory for the read-only reference coverage, asset decoding and Markdown report. The browser scripts currently use the bundled Playwright library and installed Microsoft Edge on this Windows host.

The `fetch_detail_references.py`, `import_details.py`, `complete_details.py`, `complete_weapon_stats.py`, `complete_soul_details.py`, and `fill_detail_images.py` scripts document the source collection/import work. They modify catalogs and are maintenance utilities, not startup dependencies. Review their output before replacing curated facts; rerunning an import alone can reset later curated source links or screenshots. `audit/detail-coverage.json` records the final scope and remaining gaps.

Mechanical values are not lore descriptions. Base and maximum reinforcement stats are distinct. Bonus coefficients are enabled only when published maximum base attacks match the individual weapon page. Unknown coefficients, variant defenses and image identities are never inferred from a similar name.

The runtime uses bundled JSON, images and fonts, with no Internet connection required. `localize_references.py` maintains the supplemental `articles.json` catalog; it is an optional source-import utility, not a runtime dependency. Font licenses are bundled in `assets/fonts/`.

Version 1.6.0 adds persistent catalog filters. Run `node DarkSouls-Guide/tools/verify_filters.cjs` from the parent directory for resistance/scaling order, category search, Back/refresh, empty results, Reset and mobile checks.

The full source audit uses `refresh_audit_sources.py`, `reference_audit.py` and `verify_source_facts.py`. The latter is read-only unless `--repair` is specified. Read `audit/FULL_AUDIT.md` for the exact verification scope. Source downloads remain optional maintenance files and are never fetched by the app.

The one-time roster repairs are recorded by `repair_audit_rosters.py`, `complete_ring_variants.py`, `complete_enemy_effectiveness.py` and `complete_material_acquisition.py`. Review their output before rerunning them: an import can replace later curated facts. `category_redirects.json` preserves reclassified summon routes and favorites.

Version 1.8.0 adds the Blacksmith preview. Run `node DarkSouls-Guide/tools/verify_blacksmith.cjs` from the parent directory. Read `audit/BLACKSMITH_AUDIT.md` for coverage and limits. `build_blacksmith_data.py` imports the cached Wikidot rows; `fetch_blacksmith_wiki.py` and `resume_blacksmith_sources.py` cache structured pages (the latter paces requests and backs off on rate limits); `import_blacksmith_structured.py` imports the cached templates and material schedules. Run the structured import after the Wikidot import to preserve source precedence. These utilities are never runtime network dependencies.

Version 1.9.0 adds Character Lab. Read `audit/CHARACTER_AUDIT.md` before interpreting precision claims. Run `node DarkSouls-Guide/tools/verify_character.cjs` from the parent directory. It exercises all allowed weapon rows, all individual armor levels and all ring records, alongside independent fixtures and UI interactions.

Character source maintenance, from the guide directory:

1. Preserve/review the published `audit/combat-reference.xlsx` workbook and separately cached Hollow Soldier Set wikitext. The workbook URL is recorded in the audit; downloads are optional maintenance only.
2. Run `python tools/read_combat_reference.py` to extract cached numerical cells and formulas without executing formulas.
3. After any Blacksmith import, run `python tools/build_character_data.py`. This builds `character.json`, reconciles weapon cards with Blacksmith and explicitly separates Majestic's right-hand/left-hand values. This step modifies all three catalogs.
4. Run `python tools/audit_character_parameters.py` to produce the full comparison report and regenerate the affected-preview source warnings in `character.json`.
5. Rerun Character Lab, Blacksmith, detail, filter, interaction and local-only browser checks. Audit missing records, disagreements and curated effect overrides before accepting source updates.

`build_character_data.py` alone resets disagreement annotations; always follow it with the comparison audit. Workbook per-level coefficients supersede the older maximum-only card coefficients. Individual wiki reinforcement rows remain canonical for base attack except the explicit Majestic hand variant. Source conflicts and unsupported conditional effects must not be treated as verified exact game behavior.

Version 1.9.1 fills the main catalog image gaps. `complete_images.py` imports explicitly associated Wiki.gg images, and `complete_image_variants.py` handles multi-image enemy pages, the Durgo/Greatbow alias and the four carvings. These maintenance scripts require network access, may replace curated images, and must be followed by visual review; do not run them on startup. `import_lore_images.py` copies the separately generated assets listed in `audit/generated-lore-manifest.json` into the project. All generated lore artwork remains marked as interpretive and non-canonical; never set its `image_verified` flag to true.

Run `node DarkSouls-Guide/tools/verify_images.cjs` from the parent directory. It checks active catalog asset paths, decodes new artwork in the browser, verifies generated-art labels and local-only source credits, and produces review galleries. Four unknown/unused legacy armor records remain excluded from the live armor catalog and are not given fabricated game artwork.
