# OANDA catalog + alias mapping + feed reconciliation

## Catalog

On API boot and via Arq `refresh_instruments`, Zorro fetches the **full** OANDA
instrument list. Stored fields: `canonical_id`, `display_symbol`, `asset_class`,
`tradable`. No hardcoded 11-pair enum. UI is a searchable dropdown/modal only.

Analysis always uses `canonical_id`.

## Alias map

Per MetaApi account: `canonical_id → execution_symbol`.
The Account page test-resolves against MetaApi **before save**.
Unmapped instruments: analysis OK, **execute NEVER**.

## Reconciliation

- OANDA is source of truth for prices, candles, spread, indicators.
- Twelve Data is a cross-check quote only.
- Divergence (bps > `PRICE_DIVERGENCE_BPS`) or OANDA outage:
  - block new recommendation publishing (gate G5)
  - conservative bot safety (`feed_unreliable`)
  - banner: **Price data unreliable**
- Missing numbers render as **Not available**. Never invented.
