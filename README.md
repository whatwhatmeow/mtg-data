# mtg-data

Card data, deck tools and game notes for Andrew's family Commander decks, kept in one place so they don't have to be rebuilt in every chat.

| Folder | What's in it |
|---|---|
| `data/` | Every Magic printing from Scryfall's bulk data, refreshed on the 1st of each month: name, set, collector number, mana cost, type, rules text, color identity, Commander legality, prices, plus a **Game Changer** flag and a **Marvel printing** flag. No images, tokens or art cards. |
| `query.py` | Ask questions of the card data with SQL. |
| `update.py` | The monthly refresh (run by `.github/workflows/update.yml`). |
| `sim/` | Shared deck-simulator code. |
| `decks/` | A copy of each deck in the Commander Deck Vault. |
| `collection/` | The owned-cards list (not added yet). |
| `boardgames/` | Notes per board game: rules that tripped Claude up, and lessons learned. |
| `tools/` | Helper scripts. |

## Examples

```
python query.py "SELECT name, cheapest_usd FROM oracle WHERE game_changer = 1 ORDER BY name"
python query.py "SELECT name, mana_cost FROM oracle WHERE marvel_printing = 1 AND ci_within(color_identity,'UB') AND type_line LIKE '%Instant%' LIMIT 20"
```

Prices are a snapshot from the last refresh, not live.

Card data: Scryfall (https://scryfall.com). Unofficial; not affiliated with Wizards of the Coast.
