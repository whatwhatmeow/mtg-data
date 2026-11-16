# Simulators

`common.py` holds what every deck simulator shares:

- `PROFILES`: how hard the table pushes back at Bracket 2, 3 and 4 (removal, wipes, blockers, counterspells). These are the numbers the vault simulators already used, so old and new results compare.
- `CardDB`: card text and costs from `data/cards.csv.gz`.
- `load_deck("tom-bombadil", variant="...")`: a deck (or one of its saved versions) from `decks/`.
- `compare()`, `leave_one_out()`, `show()`: run several versions of a list on the same shuffles and report win-by-turn and how many turns faster or slower each one is.

A deck's own simulator only needs a `Game` class and `play(deck, profile, rng)` that returns the turn it won.

## Deck-specific engines

The engines written so far live in `sim/vault/<id>/`, unpacked from the vault's `tools` collection by `tools/import_vault_export.py` (last import: Nov 16, 2026). Each folder has an `ABOUT.json` with how to run it, what it models and what it doesn't.

| Folder | Deck | Run |
|---|---|---|
| `doomsim` | Doom's Big Wheels | `test.py 5000` (uses its own `deck.json`) |
| `dusim` | Doom Unrivaled | `du_tools.py deck.json bracket3 4000` |
| `tomsim` | Tom's Bombs | `tom_tools.py deck.json bracket3 3000` |
| `namorsim` | Namor | `nm_loo.py bracket2 3000` |
| `wssim` | Winter Soldier | `ws_loo.py deck.json bracket2 3000` |
| `lawyersim` | Lawyers | `lawyer.py 3000` (set `CARDS_CSV=data/cards.csv.gz`) |

`python sim/vault/check.py` runs all six on today's lists in `decks/` and lists the cards each one has no model for. As of Nov 16, 2026: `dusim` is missing 31 cards of the merged Doom + Ultron list, `namorsim` 6, `wssim` 1; they only finish because the check swaps those for blanks. Not runnable: `doomsim`'s older scripts (`run.py`, `combo.py`, `b4.py`, `creatures.py`, written for sim v5) and `lawyersim/h2h.py` (needs a Saga-creature version of tomsim that was never saved to the vault).

## What these sims can't tell you

They are solitaire models: opponents remove things and block at fixed rates but don't attack, race or negotiate. Trust differences between two versions of the same deck more than the raw win turns.
