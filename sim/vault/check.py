#!/usr/bin/env python3
"""Smoke test: does every imported vault simulator still run on today's vault list?

    python sim/vault/check.py            # all simulators
    python sim/vault/check.py namorsim   # just one

Each simulator is copied to a temp folder with its deck from decks/ saved as deck.json, then its
own entry script is run with a small game count. Cards the simulator has no model for are listed
and swapped for "BLANK" (a dead card) so the run can finish; a long list there means the sim is
behind the deck and its numbers shouldn't be trusted until those cards are modeled.
"""
import importlib.util, json, os, shutil, subprocess, sys, tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
CSV = os.path.join(ROOT, "data", "cards.csv.gz")

# sim folder: (vault deck id, module holding the card tables, entry command)
SIMS = {
    "doomsim":   ("doctor-doom",         "cards",    ["test.py", "100"]),       # test.py uses its own deck.json (flat list)
    "dusim":     ("doom-unrivaled",      "du_cards", ["du_tools.py", "deck.json", "bracket3", "20"]),
    "tomsim":    ("tom-bombadil",        "tom_cards", ["tom_tools.py", "deck.json", "bracket3", "20"]),
    "namorsim":  ("namor-merfolk",       "nm_cards", ["nm_loo.py", "bracket2", "16"]),
    "wssim":     ("winter-soldier",      "ws_cards", ["ws_loo.py", "deck.json", "bracket2", "20"]),
    "lawyersim": ("lawyer-kynaios-tiro", None,       ["lawyer.py", "300"]),     # reads card data from the repo CSV
}


def known_cards(folder, module):
    spec = importlib.util.spec_from_file_location(module, os.path.join(folder, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = {"BLANK"}
    for k in dir(m):
        v = getattr(m, k)
        if k.isupper() and isinstance(v, (dict, set)) and k not in ("GAME_CHANGERS", "ANY"):
            out |= set(v)
    return out


def check(sim):
    deck_id, module, cmd = SIMS[sim]
    src = os.path.join(HERE, sim)
    d = json.load(open(os.path.join(ROOT, "decks", deck_id + ".json"), encoding="utf-8"))
    names = [c["name"] for c in d["cards"] for _ in range(int(c.get("qty", 1)))]
    if module:
        known = known_cards(src, module)
    else:
        sys.path.insert(0, os.path.join(ROOT, "sim"))
        from common import CardDB
        known = set(CardDB().cards)
    unknown = sorted(set(names) - known)
    with tempfile.TemporaryDirectory() as tmp:
        for f in os.listdir(src):
            if os.path.isfile(os.path.join(src, f)):
                shutil.copy(os.path.join(src, f), tmp)
        if sim != "doomsim":
            blanked = Counter("BLANK" if module and n in unknown else n for n in names)
            json.dump({"cards": [{"name": k, "qty": v} for k, v in blanked.items()]},
                      open(os.path.join(tmp, "deck.json"), "w", encoding="utf-8"))
        env = dict(os.environ, PYTHONHASHSEED="0", CARDS_CSV=CSV)
        r = subprocess.run([sys.executable] + cmd, cwd=tmp, env=env, capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"{'OK  ' if ok else 'FAIL'} {sim:10s} deck {deck_id} ({len(names)} cards), not modeled: {len(unknown)}")
    if unknown:
        print("       " + ", ".join(unknown))
    tail = (r.stdout if ok else r.stderr).strip().splitlines()
    print("       " + (tail[0] if ok and tail else tail[-1] if tail else "(no output)"))
    return ok


if __name__ == "__main__":
    todo = sys.argv[1:] or list(SIMS)
    sys.exit(0 if all([check(s) for s in todo]) else 1)
