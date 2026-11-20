# Deck mirror

One file per Commander Deck Vault deck, named by its vault id (`doctor-doom.json`, `tom-bombadil.json`, ...), holding exactly what the vault stores: name, owner, commanders, bracket, cards (name, qty, type, role), planned adds, notes and saved versions.

The vault is the source of truth. This copy exists so whole-vault questions can be answered with a script.

Filled from a vault export (the vault page's "Export for GitHub" button), unpacked with

```
python tools/import_vault_export.py vault-export.json
```

Last import: Nov 20, 2026 (sleeved checkmarks; decks already current). `_sleeved.json` holds the vault's sleeved checkmarks.
