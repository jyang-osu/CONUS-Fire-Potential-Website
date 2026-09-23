# CONUS / Fire potential (Beta Version)

A static dashboard for hourly potential fire behavior, fire danger indices, fuel moisture, and weather across the contiguous United States. The browser displays exported simulation results; it does not run the simulation.

**Live website:** https://jyang-osu.github.io/CONUS-Fire-Potential-Website/

## Start automatic publishing

Run from the complete local website project, not the Git repository checkout:

```powershell
cd J:\US_Fire_Potential_Behavior\Website_GitHub
.\Auto_Publish_Website.ps1
```

If PowerShell blocks script execution:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Auto_Publish_Website.ps1
```

Leave the window open, the computer awake, and the internet and simulation drive available. Codex does not need to be running. Press **Ctrl+C** to stop; avoid interrupting an upload or deployment already in progress.

The watcher checks every **300 seconds**. When a newer complete simulation hour is available, it:

1. Checks the published catalog and whether a Pages deployment is already active.
2. Exports and verifies the latest 240-hour data window.
3. Creates `site.zip` in this folder.
4. Replaces the ZIP attachment in the GitHub release tagged `web-data`.
5. Starts the **Publish CONUS dashboard** workflow on `main`.
6. Checks the published catalog on subsequent cycles to confirm the new hour is available.

It retries failed checks or updates on later cycles. During historical catch-up, it publishes the latest ready snapshot rather than every intermediate hour. Each publication uploads the entire ZIP. Only run one watcher, and do not run a separate export or manual publisher concurrently.

Optional commands:

```powershell
# Check readiness once without exporting or publishing
.\Auto_Publish_Website.ps1 -CheckOnly

# Check every minute instead of every five minutes
.\Auto_Publish_Website.ps1 -IntervalSeconds 60
```

Logs are written to `website_watch.log`. Readiness currently requires all **19 exported variables**, including the two live fuel moisture variables hidden from the interface.

## Publish immediately

Wait for any active publication to finish, then stop the watcher before running:

```powershell
.\Update_Website.ps1
```

Alternatively, double-click `Update_Website.cmd`. These perform a single export, validation, ZIP upload, and workflow dispatch. If GitHub returns the run URL, the script waits for the deployment result; otherwise it prints the Actions page so you can check the result there.

After publication, restart `Auto_Publish_Website.ps1` if continuous updates are wanted. A source-only design change does not trigger the watcher when the complete simulation hour has not advanced; use a manual publication to publish such changes immediately.

## GitHub sign-in and initial setup

Install GitHub CLI and sign in on the publishing computer. With the default Windows installation:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" auth login
& "C:\Program Files\GitHub CLI\gh.exe" auth status
```

Choose GitHub.com, HTTPS, and browser sign-in. Credentials are managed by GitHub CLI; never place passwords or tokens in project files.

The current scripts target `jyang-osu/CONUS-Fire-Potential-Website`. The repository must have:

- GitHub Pages configured with **GitHub Actions** as its source.
- The included `.github/workflows/pages.yml` workflow on `main`.
- A published release tagged `web-data`.

For a new setup, run `Export_Data.cmd`, attach `site.zip` to that release using **Attach binaries**, then run **Publish CONUS dashboard** from the Actions tab with `release_tag=web-data`.

## Local preview and export only

- `Export_Data.cmd`: export, verify, and create the ZIP without uploading it.
- `Preview.cmd`: start the local preview server.
- Preview address: http://127.0.0.1:8766/site/

Do not open the HTML directly from File Explorer; the numeric data must be served over HTTP. The preview uses the generated `site` folder. Export again after source or data changes to synchronize it.

## Portal layout and controls

| Position | Panel |
| --- | --- |
| Top left | Potential Fire Behavior |
| Top right | Fire Danger Indices |
| Bottom left | Fuel Moisture |
| Bottom right | Weather Conditions |

Panels stack on narrower screens. Each panel has independent variable, hour, and time-zone controls. **Central Time (CDT/CST)** is the default, with daylight-saving adjustment. Timestamps label interval ends.

- Black state boundaries are always visible.
- CONUS minimum, mean, and maximum appear beside each map.
- Click a grid cell to see its value and latitude/longitude, plus an hourly history chart.
- History covers 240 hourly slots ending at the selected variable's latest exported hour, independent of the selected map hour. Missing hours appear as gaps.
- **Refresh to see the latest results** reloads the page using a fresh URL and requests the latest published catalog. An open page does not automatically refresh when a new release is deployed.
- **Download map PNG** saves a colored raster image, without the interactive map's boundary and selection overlays.

The interface uses a burnt-orange and cream theme and an embedded original shield logo. NASA, USGS, and NSF logos appear below the centered acknowledgement.

### Display variables and legend ranges

| Panel | Variable | Display range |
| --- | --- | --- |
| Potential Fire Behavior | Rate of spread | 0–30 m/min |
| Potential Fire Behavior | Flame length | 0–4 m |
| Potential Fire Behavior | Fireline intensity | 0–4,000 kW/m |
| Potential Fire Behavior | Fire type | 0 suppressed/unburned; 1 surface; 2 passive crown; 3 active crown |
| Fire Danger Indices | BI | 0–120 |
| Fire Danger Indices | ERC | 0–60 |
| Fire Danger Indices | SC | 0–60 |
| Fire Danger Indices | IC | 0–100 |
| Fuel Moisture | 1-, 10-, 100-, and 1000-hour dead fuel moisture | 2–30% dry mass |
| Weather Conditions | Air temperature | −20–40 °C |
| Weather Conditions | Relative humidity | 0–100% |
| Weather Conditions | Wind speed | 0–25 m/s |
| Weather Conditions | Hourly precipitation | 0–25 mm |
| Weather Conditions | Solar radiation | 0–800 W/m² |

Dead fuel moisture and relative humidity use red for drier values and blue for wetter values. Danger indices run from green to red. Behavior magnitudes and temperature run from blue to red. Precipitation uses pale cream, green, cyan, blue, and dark blue as amounts increase.

Herbaceous and woody live fuel moisture are **hidden from the portal** pending review of their simulation. They remain in the simulation and the 19-variable export package; there are **17 selectable variables**. Wind direction, spread direction, snow cover, and snow flag are excluded from this website export.

Legend limits affect colors only. Actual values outside those limits remain available in cell values and charts. The original GeoTIFFs are not changed.

## Data window, formats, and validation

The exporter reads completed simulation receipts and verifies source checksums. It uses a shared **240-hour window** ending at the latest available output hour. Missing slots do not extend the window backward. The ZIP includes the page, catalog, and only the map assets referenced within that window; stale files are excluded.

- Source rasters: 10-km CONUS grid, EPSG:5070.
- Numeric web grids: gzip-compressed little-endian Int32 arrays, scaled by 100; `-2147483648` is NoData.
- Numeric rounding uses Float64 arithmetic before integer encoding to retain two-decimal precision for large values.
- Map images: indexed-color PNGs.
- Statistics: calculated from the source raster values.
- Validation: catalog variables, latest grids and masks against GeoTIFFs, numeric precision, PNG dimensions, referenced asset existence, hourly product counts, and site size.

The exporter applies a 950 MB referenced-asset budget and validation checks that the generated site is under 1 GB. Large release assets are kept out of Git history. A clicked-cell chart can fetch up to 240 grids, so the first chart may take time to load. Use a modern browser supporting gzip `DecompressionStream`.

## Project and repository folders

**Working project:** `J:\US_Fire_Potential_Behavior\Website_GitHub`

**Source repository:** `J:\US_Fire_Potential_Behavior\Github_repository\CONUS-Fire-Potential-Website`

Edit and test in the working project, copy changed source files to the repository, and use GitHub Desktop to **Commit → Push origin**. Copying between these folders is not automatic.

Publishing and committing serve different purposes:

- `Update_Website.ps1` and the watcher publish the locally generated ZIP; they do **not** commit or push source files.
- Committing and pushing preserve source history; the current workflow does **not** publish automatically on push.
- Changes made only in the repository checkout are not used by the working project's exporter.

Do not commit `runtime`, `site`, `site.zip`, logs, or temporary lock files. The repository checkout alone cannot run the bundled-runtime launchers. Keep the complete working project when transferring export and publishing capability to another computer.

### Important files

| File or folder | Purpose |
| --- | --- |
| `Auto_Publish_Website.ps1` / `watch_website.py` | Continuous publishing watcher |
| `Update_Website.ps1` / `Update_Website.cmd` | Single publication |
| `Export_Data.cmd` | Export and package without publication |
| `Preview.cmd` | Local preview server |
| `web/index.html` | Portal source with embedded map geometry and logos |
| `web/assets` | Agency logo originals and source URLs |
| `CONUS_Fire_Potential_Logo.svg` | Original portal logo |
| `source_reader.py` | Simulation inventory and legend metadata |
| `export_site.py` | Numeric and PNG export, catalog, stale asset cleanup |
| `verify_site.py` | Export validation |
| `package_site.py` | Latest-240-hour ZIP assembly |
| `static-adapter.js` | Static data adapter reference; active code is embedded in the HTML |
| `config.json` | Simulation location and export worker count |
| `site` / `site.zip` | Generated website and release package |
| `runtime` | Standalone local Python environment |
| `.github/workflows/pages.yml` | Release download and GitHub Pages deployment |

`config.json` currently uses `simulation_root: ../Combined_CONUS` and `export_workers: 6`. Update the simulation path when relocating the working project. The preview launcher uses port 8766. When moving to another GitHub repository, update the repository references in the publishing scripts and the catalog URL in the watcher.

## Troubleshooting

- **Website shows an older hour:** check the watcher log, validation result, and Actions deployment. Browser refresh only shows already-published data.
- **Old layout persists:** use the portal refresh button or Ctrl+Shift+R.
- **Validation fails:** publication stops before upload. Read the variable/time/error in the message; do not disable validation. The large-value rounding issue was corrected in the exporter.
- **HRRR input is delayed:** the simulation must finish the new hour before publication can start.
- **Another watcher is running:** use the existing window instead of starting a duplicate.
- **Source-only change is not published:** run a single manual update after stopping the idle watcher.

## Contacts and acknowledgement

**Contact:**

Jia Yang — jia.yang11@okstate.edu  
Xiaohao Jiao — xiaohao.jiao@okstate.edu  
Department of Natural Resource Ecology and Management  
Oklahoma State University

**Acknowledgement:** This work is supported by NASA, USGS, and NSF.

The portal is a beta research product. Potential fire behavior assumes a fire occurs; it does not predict ignition locations or fire perimeters. Warm-up results and display ranges should not be interpreted as official operational danger classifications.