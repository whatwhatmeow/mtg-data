# Simulators

`common.py` holds what every deck simulator shares:

- `PROFILES`: how hard the table pushes back at Bracket 2, 3 and 4 (removal, wipes, blockers, counterspells). These are the numbers the vault simulators already used, so old and new results compare.
- `CardDB`: card text and costs from `data/cards.csv.gz`.
- `load_deck("tom-bombadil", variant="...")`: a deck (or one of its saved versions) from `decks/`.
- `compare()`, `leave_one_out()`, `show()`: run several versions of a list on the same shuffles and report win-by-turn and how many turns faster or slower each one is.

A deck's own simulator only needs a `Game` class and `play(deck, profile, rng)` that returns the turn it won.

## Deck-specific engines

The engines written so far (Doctor Doom, Doom Unrivaled, Tom's Bombs, Namor, the Lawyers, Winter Soldier and others) are stored in the vault's `tools` collection. `tools/import_vault_export.py` unpacks them into `sim/vault/<id>/` from a vault export file. They have not been imported yet.

## What these sims can't tell you

They are solitaire models: opponents remove things and block at fixed rates but don't attack, race or negotiate. Trust differences between two versions of the same deck more than the raw win turns.
