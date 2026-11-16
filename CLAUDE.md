# mtg-data: read this first (it replaces exploring the repo)

Andrew's one home for the things Claude kept rebuilding. Don't list files or read the README; use this map.

| Need | Where | How |
|---|---|---|
| Card text, legality, prices, Game Changer, Marvel printing | `data/cards.csv.gz` (one row per printing) | `python query.py "SQL"`; table `cards`, view `oracle` (one row per card) |
| Simulate a deck | `sim/` | `sim/common.py` for profiles, deck loading, paired comparisons; deck-specific engines in `sim/vault/<id>/` |
| A vault decklist | `decks/<doc_id>.json` | read with Python; never print a whole deck into the chat |
| What Andrew owns | `collection/` | not imported yet; ask before assuming ownership |
| Board game coaching | `boardgames/<game>.md` | read the game's page before giving any advice |

## Card data
- Columns: id, oracle_id, name, set_code, set_name, collector_number, released_at, rarity, layout, mana_cost, cmc, type_line, oracle_text, power, toughness, loyalty, color_identity (letters, e.g. `BRU`), keywords, commander_legality, price_usd, price_usd_foil, price_usd_etched, finishes, promo, promo_types, digital, game_changer, marvel.
- `oracle` view adds cheapest_usd, printings, sets, game_changer, marvel_printing.
- Helpers: `ci_within(color_identity,'UBR')`, `ci_has(color_identity,'U')`.
- Marvel-only decks: `WHERE marvel_printing = 1`. A card counts if any printing is from a Marvel product, even when Andrew's copy is an older printing. Rule and limits are documented at the top of `update.py`; hand-add missed Secret Lair drops in `data/marvel_extra.json`.
- Bracket checks: `WHERE game_changer = 1`. Never check the Game Changers list on the web.
- Prices are from the last refresh (`data/meta.json`), not live. Weekly prices live in the separate `mtg-prices` repo.
- Always `LIMIT` queries and select only the columns needed.

## Decks
- `decks/` mirrors the Commander Deck Vault (artifact `48f5fbde-afec-4fad-ab09-ffafadbe3d1b`). The vault stays the source of truth.
- After every vault write, make the same change to `decks/<doc_id>.json` and commit it in the same session.
- Whole-vault questions ("which deck wants this card?") are answered from `decks/` with a Python script, never with `db_list`.

## Simulators
- New sim: write only the `Game` class and a top-level `play(deck, profile, rng)`; import everything else from `sim/common.py`. Save it under `sim/<deck id>/` and commit, so it is never rewritten.
- Use `PYTHONHASHSEED=0` and the paired-seed `compare()` so runs are repeatable.

## Board games
- Each page lists rules Claude has gotten wrong and Andrew's lessons. Append to the page at the end of every coaching session and commit.

## Committing
- Andrew is new to GitHub: commit and push to `main` yourself; don't hand him branches or pull requests.
- `git pull --rebase` first: two scheduled jobs also commit here (monthly card data) and in `mtg-prices` (weekly prices).
