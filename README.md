# MTG card data

Monthly snapshot of every Magic printing (from Scryfall bulk data), slimmed to:
name, set, collector number, mana cost, type, oracle text, color identity,
Commander legality, prices (USD / foil / etched), plus a few research extras
(cmc, P/T, keywords, rarity, promo types so Secret Lairs are findable).
Tokens, emblems and art-series cards are excluded; no images.

- `data/cards.csv.gz` - the data (created by the first workflow run)
- `scripts/update.py` - downloads + slims the data
- `scripts/query.py` - run SQL against it
- `.github/workflows/update.yml` - runs update.py on the 1st of each month

Prices are a snapshot from the last run, not live.

Data: Scryfall (https://scryfall.com). Unofficial; not affiliated with Wizards of the Coast.
