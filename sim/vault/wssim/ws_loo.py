"""Paired leave-one-out and swap tests for Winter Soldier lists."""
import json, random, math, sys
from multiprocessing import Pool
from ws_sim import Game, PROFILES
from ws_cards import LANDS

N = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
DECKFILE, PROF = sys.argv[1], sys.argv[2]
d = json.load(open(DECKFILE))
base = [c["name"] for c in d["cards"] for _ in range(c.get("qty", 1))]
nonland = sorted({c for c in base if c not in LANDS})

def play(deck):
    return [(Game(deck, PROFILES[PROF], random.Random(9_000_011 * (k + 1))).run()["win"] or 99) for k in range(N)]

def job(card):
    deck = list(base)
    if card:
        deck[deck.index(card)] = "BLANK"
    return card, play(deck)

if __name__ == "__main__":
    with Pool() as p:
        R = dict(p.map(job, [None] + nonland, chunksize=1))
    b = R[None]
    cap = lambda x: min(x, 17)
    rows = []
    for c in nonland:
        dt = [cap(x) - cap(y) for x, y in zip(R[c], b)]
        m = sum(dt) / N
        se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
        d12 = (sum(y <= 12 for y in b) - sum(x <= 12 for x in R[c])) / N
        rows.append((c, m, se, d12))
    rows.sort(key=lambda r: -r[1])
    out = {"base_by12": sum(y <= 12 for y in b) / N, "base_by16": sum(y <= 16 for y in b) / N, "rows": rows}
    json.dump(out, open(f"loo_{DECKFILE.replace('.json','')}_{PROF}.json", "w"))
    print(f"base by12 {out['base_by12']:.3f} by16 {out['base_by16']:.3f}")
    for c, m, se, d12 in rows:
        print(f"{c:36s} {m:+.3f}±{se:.3f}  by12 {100*d12:+.1f}pts")
