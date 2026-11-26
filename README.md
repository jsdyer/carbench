# Car Bench

Compare Canadian vehicle energy and ownership scenarios using real NRCan fuel-consumption, battery-electric and plug-in-hybrid ratings. Keyless monthly collection; all personal calculations run locally.

<!-- coolcode:guide -->
Choose a model year and search any make, model or vehicle class; compare up to three variants. Enter annual kilometres, city driving share, local fuel prices and home/public charging costs. Plug-in hybrids include both electricity and any reported fuel use in charged mode. Add each vehicle's purchase price, expected resale and annual insurance/maintenance to compare an ownership period. Prices begin as editable examples; purchase and other costs begin at zero. Explicitly saved comparisons preserve original source records and capture dates. CSV exports include assumptions.
<!-- /coolcode:guide -->

## Sources and coverage

[NRCan fuel consumption ratings, Open Canada](https://open.canada.ca/data/en/dataset/98f1a129-f628-4ce4-b24d-6f16bf24dd64), under the Open Government Licence. Five current English CSV resource IDs are configured in `config/sources.json`: fuel/conventional hybrids 2015–2024, 2025 and 2026; BEV and PHEV 2012–2026. The collector obtains their current download URLs from CKAN metadata, validates headers, numbers, minimum coverage and expected HTTPS host, and records hashes and actual resource edition dates. It never substitutes collection time for source update time. Failed fetches/parsing fail the workflow and do not deploy partial data.

Records are deduplicated by model-variant identity and sharded by year in `web/data/`. The app derives all years, counts and search choices from those real records. 2012–2014 contain only electric/PHEV catalogues. Source tables can omit or change models. Standard lab ratings are not actual driving measurements. No prices or guarantees are implied.

## Calculation

Fuel litres = annual kilometres / 100 × city/highway-weighted L/100km. Electric use = applicable kilometres / 100 × combined kWh/100km. PHEV charged-mode distance is an explicit assumption and includes its reported simultaneous fuel component; the other distance uses gasoline-mode ratings. Public charging prices are weighted by the share of charging energy. A sensitivity multiplier applies to consumption without claiming to model weather. Annual costs combine energy and visitor-entered other costs; period totals add purchase, subtract resale and multiply annual running costs. Financing, changing energy prices and emissions calculations are excluded.

## Expand or customize

Add resource IDs and their `fuel`, `electric` or `plugin` schema kind to `config/sources.json`, then run `python3 scripts/refresh.py`. Schema changes must be handled and tested explicitly. Do not substitute original two-cycle pre-2015 ratings into the same comparison. Update the README coverage when adding years. Run the Pages workflow manually to collect and publish; scheduled checks run monthly. No API keys are required.

The default build uses the committed snapshot and is offline. The first main push captures data if no snapshot is committed. Later source-change pushes publish the saved edition; schedules and manual runs capture fresh data, commit the validated snapshot and publish it. A dedicated schedule guard keeps only this collector active. Register `.github/workflows/pages.yml` with the hub watchdog and a freshness check on `/carbench/data/index.json` → `capturedAt` (45 days).

## Development and privacy

Run `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests -v`, `python3 scripts/build.py`; browser checks run in CI. Main builds deploy with GitHub Pages Actions. Inputs stay on the device. Explicit saves use `coolcode:carbench:comparison:v1` and can be deleted. The standard visit counter receives the tool ID, not vehicle choices or costs.

## Ready-to-use example

[Electric Car Energy Costs in Canada](https://coolcode.ca/carbench/electric-car-ratings.html) opens this scenario in the same tool. See the annual electricity cost for a battery electric vehicle from the published Canadian ratings. The example uses 20,000 km a year. Change the vehicle, distance or charging prices to compare your own costs.
