# Deck mirror

One file per Commander Deck Vault deck, named by its vault id (`doctor-doom.json`, `tom-bombadil.json`, ...), holding exactly what the vault stores: name, owner, commanders, bracket, cards (name, qty, type, role), planned adds, notes and saved versions.

The vault is the source of truth. This copy exists so whole-vault questions can be answered with a script.

Not filled yet: it needs a vault export file, unpacked with

```
python tools/import_vault_export.py vault-export.json
```
