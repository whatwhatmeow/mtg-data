import json, random, math, sys
from multiprocessing import Pool
from nm_sim import Game, PROFILES
from nm_cards import C, LANDS

def load(f):
    d = json.load(open(f))
    return [c["name"] for c in d["cards"] for _ in range(c.get("qty", 1))]

def check(deck):
    bad = [c for c in deck if c not in C and c not in LANDS]
    assert not bad, bad
    assert len(deck) == 99, len(deck)

def play(deck, prof, N, seed=9_000_011):
    out = []
    for k in range(N):
        out.append(Game(deck, PROFILES[prof], random.Random(seed * (k + 1))).run())
    return out

def _job(a):
    name, deck, prof, N, s = a
    return name, play(deck, prof, N, s)

def compare(variants, prof, N=5000, chunks=8):
    names = list(variants)
    jobs = []
    for n in names:
        per = N // chunks
        for j in range(chunks):
            jobs.append((n, variants[n], prof, per, 9_000_011 + 7919 * j))
    with Pool() as p:
        res = p.map(_job, jobs, chunksize=1)
    R = {n: [] for n in names}
    for n, r in res:
        R[n] += r
    base = R[names[0]]
    rows = []
    cap = lambda x: min(x or 99, 17)
    for n in names:
        r = R[n]
        w = [x["win"] for x in r]
        dt = [cap(b["win"]) - cap(x) for x, b in zip(w, base)]
        m = sum(dt) / len(dt)
        se = math.sqrt(sum((v - m) ** 2 for v in dt) / (len(dt) - 1) / len(dt))
        rows.append(dict(name=n, by10=sum((x or 99) <= 10 for x in w) / len(w),
                         by12=sum((x or 99) <= 12 for x in w) / len(w),
                         by16=sum((x or 99) <= 16 for x in w) / len(w),
                         avg=sum(cap(x) for x in w) / len(w), faster=m, se=se,
                         namor_removed=sum(x["namor_removed"] for x in r) / len(r),
                         countered=sum(x["countered"] for x in r) / len(r),
                         wiped=sum(x["wiped"] for x in r) / len(r),
                         first_hit=sum((x["first_hit"] or 17) for x in r) / len(r),
                         max_namor=sum(x["max_namor"] for x in r) / len(r)))
    return rows

def show(rows, title=""):
    print("==", title)
    for r in rows:
        print(f"  {r['name']:42s} by10 {100*r['by10']:5.1f}% by12 {100*r['by12']:5.1f}% by16 {100*r['by16']:5.1f}% "
              f"avg {r['avg']:5.2f} faster {r['faster']:+.3f}±{r['se']:.3f} cntr {r['countered']:.2f} namorKO {r['namor_removed']:.2f}")

def swap(deck, pairs):
    x = list(deck)
    for o, i in pairs:
        x[x.index(o)] = i
    return x
