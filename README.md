# WealthDashboard

A personal portfolio dashboard with a new portfolio-first interface.

**Start:** Open `index.html` (the new default dashboard). The interface supports light and dark themes and reads the existing local browser data from `portfolio-tracker-v1`.

## New dashboard

- Portfolio overview with market value, invested capital, unrealized P/L and open positions
- Portfolio history chart with selectable time ranges, using dated snapshots
- Positions table with quantity, average buy-in, current price, market value and P/L
- Transaction history for contributions and internal transfers
- Allocation analytics by asset type, positions, region, sector, industry, country and currency (unavailable classifications are shown as unclassified rather than guessed)
- Trading 212 read-only sync through the existing Homeserver bridge
- JSON backup and restore

## Existing workspace retained

Open `portfolio-tracker.html` for the full compatibility workspace. It retains the established Trading 212 CSV importer and import history, dated CSV snapshots, savings pots, target allocations, rebalancing, contribution tracking, calculator, Monte Carlo simulation, goal calculator, crash test and monthly budget.

Both interfaces use the same local portfolio storage. CSV imports made in the classic workspace appear in the new dashboard after refreshing it.

## Trading 212 bridge

The new dashboard connects to the existing `trading212-bridge/` Docker/FastAPI service. API credentials remain on the Homeserver. The connection is read-only and cannot place trades or move money.

## Data and privacy

Portfolio data is stored in the browser's localStorage. Use Export JSON regularly to create a backup. Importing a backup replaces the current portfolio data in this browser.

No live market-data provider is bundled into the dashboard; displayed prices and values come from imported snapshots or the connected Trading 212 bridge.

This project is a personal tracking tool, not investment advice.

## Dividend forecast (Vercel deployment)

The new dashboard includes a CSV-based dividend forecast at `#dividends`. It accepts a positions CSV with columns such as `Ticker` / `Symbol` and `No. of shares` / `Quantity`. Tickers are sent to the server-side `/api/dividends` function; provider credentials are never exposed to the browser.

### Required configuration

Deploy the repository as a Vercel Git project and add the environment variable `EODHD_API_TOKEN` in the Vercel project settings (Production and Preview as appropriate). The API uses EOD Historical Data's dividend history/corporate actions endpoint and Frankfurter reference FX rates to convert declared dividend amounts into EUR. Without this environment variable the endpoint returns a setup message and no live dividend data can be retrieved.

The forecast sums announced distributions in the next 12 months. If no future distribution is announced, it estimates a 12-month amount from the latest historical distribution and its reported cadence (or inferred cadence). The dashboard labels such results as estimates. Net values are a configurable simple tax haircut (default 26.375%), not an individualized German tax calculation. FX uses current reference rates rather than payment-date exchange rates. Provider coverage and ticker mapping are not guaranteed for every exchange or ETF.
