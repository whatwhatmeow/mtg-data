#!/usr/bin/env python3
"""Unpack a Commander Deck Vault export into the repo.

  python tools/import_vault_export.py vault-export.json

Expects {"decks": {id: deck}, "tools": {id: tool}} (lists of {"id":..., "data":...} also work).
Writes decks/<id>.json (one deck per file, exactly as stored in the vault) and
sim/vault/<tool id>/<file> for every simulator file, plus sim/vault/<tool id>/ABOUT.json
with its howto / modeled / not_modeled notes. The vault's "sleeved" checkmarks, if present,
go to decks/_sleeved.json.

A simulator is skipped when the repo copy is newer (its ABOUT.json "updated" date is later than the
vault's): simulators are edited here now, and the vault may only hold an older version.
"""
import datetime, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def docs(x):
    if isinstance(x, dict):
        return x.items()
    return [(d["id"], d.get("data", d)) for d in x or []]


def day(s):
    """'Nov 16, 2026 (...)' or '2026-11-16' -> date; None if there is no date in it."""
    m = re.search(r"([A-Z][a-z]{2})[a-z]* (\d{1,2}), (\d{4})", s or "")
    if m:
        try:
            return datetime.datetime.strptime(" ".join(m.groups()), "%b %d %Y").date()
        except ValueError:
            return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return datetime.date(*map(int, m.groups())) if m else None


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
        about = os.path.join(out, "ABOUT.json")
        if os.path.exists(about):
            mine, theirs = day(json.load(open(about, encoding="utf-8")).get("updated")), day(t.get("updated"))
            if mine and theirs and mine > theirs:
                print(f"  kept repo copy of {i} ({mine} is newer than the vault's {theirs})")
                continue
        os.makedirs(out, exist_ok=True)
        for name, src in (t.get("files") or {}).items():
            with open(os.path.join(out, os.path.basename(name)), "w", encoding="utf-8") as f:
                f.write(src)
        with open(os.path.join(out, "ABOUT.json"), "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in t.items() if k != "files"}, f, indent=1, ensure_ascii=False)
        nt += 1
    if ex.get("sleeved"):
        with open(os.path.join(ROOT, "decks", "_sleeved.json"), "w", encoding="utf-8") as f:
            json.dump(ex["sleeved"], f, indent=1, ensure_ascii=False)
    print(f"{nd} decks -> decks/, {nt} simulators written to sim/vault/")


if __name__ == "__main__":
    main(sys.argv[1])
