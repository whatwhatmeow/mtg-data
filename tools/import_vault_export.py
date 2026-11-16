#!/usr/bin/env python3
"""Unpack a Commander Deck Vault export into the repo.

  python tools/import_vault_export.py vault-export.json

Expects {"decks": {id: deck}, "tools": {id: tool}} (lists of {"id":..., "data":...} also work).
Writes decks/<id>.json (one deck per file, exactly as stored in the vault) and
sim/vault/<tool id>/<file> for every simulator file, plus sim/vault/<tool id>/ABOUT.json
with its howto / modeled / not_modeled notes.
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def docs(x):
    if isinstance(x, dict):
        return x.items()
    return [(d["id"], d.get("data", d)) for d in x or []]


def main(path):
    ex = json.load(open(path, encoding="utf-8"))
    os.makedirs(os.path.join(ROOT, "decks"), exist_ok=True)
    nd = nt = 0
    for i, d in docs(ex.get("decks")):
        with open(os.path.join(ROOT, "decks", i + ".json"), "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1, ensure_ascii=False)
            f.write("\n")
        nd += 1
    for i, t in docs(ex.get("tools")):
        while "files" not in t and isinstance(t.get("data"), dict):
            t = t["data"]          # one tool was saved with an extra wrapper
        out = os.path.join(ROOT, "sim", "vault", i)
        os.makedirs(out, exist_ok=True)
        for name, src in (t.get("files") or {}).items():
            with open(os.path.join(out, os.path.basename(name)), "w", encoding="utf-8") as f:
                f.write(src)
        with open(os.path.join(out, "ABOUT.json"), "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in t.items() if k != "files"}, f, indent=1, ensure_ascii=False)
        nt += 1
    print(f"{nd} decks -> decks/, {nt} simulators -> sim/vault/")


if __name__ == "__main__":
    main(sys.argv[1])
