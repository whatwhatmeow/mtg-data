import json, random, math, sys
from multiprocessing import Pool
from tom_sim import Game, PROFILES
from tom_cards import LANDS

def load(f):
    d = json.load(open(f))
    return [c["name"] for c in d["cards"] for _ in range(c.get("qty", 1))]

def save(deck, f):
    from collections import Counter
    json.dump({"cards": [{"name": k, "qty": v} for k, v in sorted(Counter(deck).items())]}, open(f, "w"))

def swap(deck, pairs):
    x = list(deck)
    for o, i in pairs:
        x[x.index(o)] = i
    return x

def play(deck, prof, N, seed=5_000_011, combo_from=1):
    out = []
    for k in range(N):
        s = Game(deck, PROFILES[prof], random.Random(seed * (k + 1)), combo_from=combo_from).run()
        out.append((s["win"] or 99, s["how"] or "none"))
    return out

def _job(a):
    name, deck, prof, N, cf = a
    return name, play(deck, prof, N, combo_from=cf)

def compare(V, prof, N=3000, combo_from=1):
    names = list(V)
    with Pool() as p:
        R = dict(p.map(_job, [(n, V[n], prof, N, combo_from) for n in names], chunksize=1))
    b = R[names[0]]
    cap = lambda x: min(x, 17)
    rows = []
    for n in names:
        r = R[n]
        dt = [cap(y[0]) - cap(x[0]) for x, y in zip(r, b)]
        m = sum(dt) / N
        se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
        combo = sum(1 for x in r if x[1].startswith("combo") or x[1] in ("helix", "mazes_end")) / N
        rows.append(dict(name=n, by8=sum(x[0] <= 8 for x in r) / N, by10=sum(x[0] <= 10 for x in r) / N,
                         by12=sum(x[0] <= 12 for x in r) / N, by16=sum(x[0] <= 16 for x in r) / N,
                         combo=combo, faster=m, se=se))
    return rows

def show(rows, title=""):
    print("==", title, flush=True)
    for r in rows:
        print(f"  {r['name']:44s} by8 {100*r['by8']:4.1f}% by10 {100*r['by10']:5.1f}% by12 {100*r['by12']:5.1f}% by16 {100*r['by16']:5.1f}% combo-wins {100*r['combo']:4.1f}%  faster {r['faster']:+.3f}±{r['se']:.3f}", flush=True)

def loo(deckf, prof, N=3000):
    base = load(deckf)
    nonland = sorted({c for c in base if c not in LANDS})
    V = {"base": base}
    for c in nonland:
        x = list(base); x[x.index(c)] = "BLANK"; V[c] = x
    rows = compare(V, prof, N)
    b = rows[0]
    rest = sorted(rows[1:], key=lambda r: r["faster"])     # most negative = card matters most
    print(f"base by12 {b['by12']:.3f} by16 {b['by16']:.3f}")
    for r in rest:
        print(f"{r['name']:36s} {-r['faster']:+.3f}±{r['se']:.3f}  by12 {100*(b['by12']-r['by12']):+.1f}pts")

if __name__ == "__main__":
    loo(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3000)
