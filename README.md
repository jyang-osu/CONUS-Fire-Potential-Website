# CONUS dashboard for GitHub Pages

This is a separate static version of the local portal. The website needs no Python server, no J: drive access, and no external map services. It includes all 19 variables, four result families, state boundaries, WGS84 cell coordinates, CONUS statistics, time-zone selection, four independent family panels, and ten-day clicked-cell plots.

## Use locally

1. Double-click **Export_Data.cmd**. This reads the completed simulation outputs configured in config.json. It creates site/ and site.zip. The simulation and local portal are not modified.
2. Double-click **Preview.cmd**.
3. Open **http://127.0.0.1:8766/site/**. Keep that console open. Ctrl+C stops the preview.

Do not open index.html directly with a file:// URL: browsers require HTTP to fetch the numeric files.

## Publish to GitHub Pages

1. Create a GitHub repository and upload/commit the source files in this folder, including the hidden .github folder and web folder. Do NOT commit runtime/, site/, or site.zip. They are excluded in .gitignore.
2. In the repository's **Settings → Pages → Build and deployment**, select **GitHub Actions**.
3. Create a release with tag **web-data**, and attach the generated **site.zip** as a release asset. The ZIP contains index.html at its root.
4. Open **Actions → Publish CONUS dashboard → Run workflow** and use release_tag **web-data**.
5. The successful deployment displays your GitHub Pages URL.

The generated site is not published automatically by this local project. No repository or account has been created or changed. Publishing makes the displayed simulation products accessible according to the repository's Pages visibility.

## Update the website

Run Export_Data.cmd after new simulation hours are complete. Replace the site.zip release asset with the new package, then run the publishing workflow again. Reloading the browser reads the latest published export, not the live simulation. There is no in-page Refresh button.

The exporter uses one shared 240-hour window ending at the newest completed GeoTIFF hour across all variables. The ZIP includes only catalog-listed assets inside that window. Missing slots remain gaps; they do not extend the time window. Export is a snapshot: outputs still being written can be omitted until the next export.

Large data packages stay in release assets, avoiding growth of Git source history. GitHub Pages has an approximately 1 GB published-site limit; the exporter checks a conservative 950 MB asset budget and stops before replacing the catalog if exceeded.

## Files and formats

- **web/index.html**: static dashboard source, including boundary outlines and cell-center coordinates.
- **export_site.py**: local exporter with checksum verification, PNG generation, numeric export, and stale-data cleanup.
- **source_reader.py**: independent output catalog reader and variable definitions.
- **config.json**: simulation_root and export_workers (default 6).
- **site/**: complete generated website; contains no Python or GeoTIFF source data.
- **site/catalog.json**: variables, units, completed hours, statistics, raster geometry, hashes, and relative data links.
- **site/data/**: transparent map PNGs plus gzip-compressed little-endian Int32 row-major grids scaled by 100 (two decimal places); -2147483648 means NoData.
- **site.zip**: deployable release asset.
- **runtime/**: local bundled Python dependencies; never upload to Pages.
- **.github/workflows/pages.yml**: manual release-asset deployment workflow.

The browser reconstructs interactive maps from numeric arrays so clicked values are independent of map colors. PNGs provide downloadable map images without state-line or label overlays. Web values are rounded to two decimal places, including values above the legend maximum; original GeoTIFFs retain full precision. Summary statistics are calculated from the original float data. Source GeoTIFFs remain in Combined_CONUS for GIS analysis.

The history chart may fetch up to 240 compressed grids for the chosen variable; first-time charts can take longer on slow connections. Requests are limited to six at a time and a small memory cache. A modern browser supporting DecompressionStream is required.

Time selection is restricted to the newest ten-day window for each variable. Charts always end at that variable's latest exported hour, independently of the map hour. UTC data keys are converted for display using the selected regional time zone and daylight-saving rules.

## Transfer and independence

Keep this complete local folder if the recipient needs to export or preview. Change simulation_root in config.json if results are stored elsewhere. Only site/ contents are required to host the published website. The exporter uses the supplied runtime and source_reader.py, not the Website_CONUS code or environment.

## Hosting documentation

- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

The included results are model outputs and may remain in warm-up. Map colors are display ranges, not official operational danger classes.


The GitHub version excludes wind direction (WDIR_vector_mean), spread_direction, SNOWC, and SNOW_FLAG. These variables remain in the simulation and local portal.

## One-click publication

Run Update_Website.cmd from the complete Website_GitHub folder after signing in with GitHub CLI. It exports, verifies, packages, replaces the web-data release asset, and starts the Pages workflow for jyang-osu/CONUS-Fire-Potential-Website. If GitHub returns a run URL, it waits for the deployment result; otherwise it prints the Actions page for checking. Keep the console open until completion. No commit is needed for data updates. This is a manual update, not a scheduled job. Do not run a separate export concurrently.


## Continuous PowerShell publishing

Run .\Auto_Publish_Website.ps1 from this complete Website_GitHub folder. It checks every 300 seconds for a newer hour containing all 19 variables in completed receipts, compares against the live website, and invokes Update_Website.ps1 only when needed. Leave PowerShell open and the computer awake. Ctrl+C stops it. Codex is not required. Use -CheckOnly for one read-only readiness check, or -IntervalSeconds 60 to check each minute. Failures retry; website_watch.log records checks. Existing deployments are allowed to finish before another update. Each update uploads the full ZIP. During historical catch-up, it publishes the latest ready snapshot rather than deploying every intermediate hour.



## Dashboard layout

Four panels display fuel moisture, fire danger indices, fire behavior, and weather conditions. Each panel has independent variable, hour, and time-zone controls, a map, CONUS statistics, and clicked-cell history. Panels use two columns on wide screens and stack on narrower screens. Black state boundaries are always visible. Reload the browser to load a newer published snapshot.
