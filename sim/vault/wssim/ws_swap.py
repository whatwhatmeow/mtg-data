"""Paired swap tests: each candidate replaces a chosen slot."""
import json, random, math, sys
from multiprocessing import Pool
from ws_sim import Game, PROFILES

def load(f):
    d = json.load(open(f))
    return [c["name"] for c in d["cards"] for _ in range(c.get("qty", 1))]

def play(deck, prof, N, seed=9_000_011):
    return [(Game(deck, PROFILES[prof], random.Random(seed * (k + 1))).run()["win"] or 99) for k in range(N)]

def _job(a):
    name, deck, prof, N = a
    return name, play(deck, prof, N)

def compare(variants, prof, N=3000):
    """variants: dict name -> deck (first is baseline)."""
    names = list(variants)
    with Pool() as p:
        R = dict(p.map(_job, [(n, variants[n], prof, N) for n in names], chunksize=1))
    b = R[names[0]]
    cap = lambda x: min(x, 17)
    out = []
    for n in names:
        r = R[n]
        dt = [cap(y) - cap(x) for x, y in zip(r, b)]     # positive = faster than baseline
        m = sum(dt) / N
        se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
        out.append(dict(name=n, by10=sum(x <= 10 for x in r) / N, by12=sum(x <= 12 for x in r) / N,
                        by16=sum(x <= 16 for x in r) / N, faster=m, se=se))
    return out

def swap(deck, pairs):
    x = list(deck)
    for o, i in pairs:
        x[x.index(o)] = i
    return x

def show(rows, title=""):
    print("==", title)
    for r in rows:
        print(f"  {r['name']:44s} by10 {100*r['by10']:5.1f}% by12 {100*r['by12']:5.1f}% by16 {100*r['by16']:5.1f}%  faster {r['faster']:+.3f}±{r['se']:.3f}")
