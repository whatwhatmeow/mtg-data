"""Doom Unrivaled: Owned build vs Unique Pact (Nov 20, 2026).

PYTHONHASHSEED=0 python3 pact_compare.py 10000 bracket3 bracket4
Reads ../../../decks/doom-unrivaled.json and builds four lists: the Owned build, the Unique Pact
version, the Owned build with Tainted Pact (28 Swamps), and the singleton lands without Pact.
"""
import json, math, os, random, sys
from collections import Counter
from multiprocessing import Pool
from du_sim import Game, PROFILES
from du_cards import LANDS

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "..", "..", "..", "decks", "doom-unrivaled.json")

def version(d, vid):
    main = Counter({c["name"]: c["qty"] for c in d["cards"]})
    v = next(x for x in d["variants"] if x["id"] == vid)
    for c in v["out"]: main[c["name"]] -= c.get("qty", 1)
    for c in v["in"]: main[c["name"]] += c.get("qty", 1)
    return [k for k, n in (+main).items() for _ in range(n)]

def job(a):
    name, deck, prof, N = a
    return name, [(s["win"] or 99, s["how"] or "none") for s in
                  (Game(deck, PROFILES[prof], random.Random(3_000_017 * (k + 1))).run() for k in range(N))]

if __name__ == "__main__":
    d = json.load(open(DECK))
    owned, uniq = version(d, "owned-build"), version(d, "unique-pact")
    V = {"Owned build": owned, "Unique Pact": uniq,
         "Owned + Pact (Swamps)": [c for c in owned if c != "Chromatic Sphere"] + ["Tainted Pact"],
         "Unique lands, no Pact": [c for c in uniq if c != "Tainted Pact"] + ["Chromatic Sphere"]}
    for k, v in V.items(): assert len(v) == 99, (k, len(v))
    N = int(sys.argv[1])
    for prof in sys.argv[2:]:
        with Pool() as p:
            R = dict(p.map(job, [(n, V[n], prof, N) for n in V], chunksize=1))
        base = R["Owned build"]
        print("==", prof, N, "games")
        for n, r in R.items():
            dt = [min(y[0], 17) - min(x[0], 17) for x, y in zip(base, r)]
            m = sum(dt) / N; se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
            f = lambda t: 100 * sum(x[0] <= t for x in r) / N
            print(f"  {n:24s} T6 {f(6):4.1f}%  T8 {f(8):4.1f}%  T10 {f(10):4.1f}%  T16 {f(16):4.1f}%  turns vs Owned {m:+.2f}±{se:.2f}")
