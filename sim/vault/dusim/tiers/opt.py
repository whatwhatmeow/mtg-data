import os
import sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

def pstats(base, r):
    dt = [min(y, 17) - min(x, 17) for x, y in zip(base, r)]
    m = sum(dt) / len(dt); se = math.sqrt(sum((v - m) ** 2 for v in dt) / (len(dt) - 1) / len(dt))
    return m, se

def swap(d, o, i):
    x = list(d); x[x.index(o)] = i; return x

def optimize(deck, prof, feasible, pool, rounds=4, Ns=1000, Nv=4000, protect=(), log=print, k_max=5):
    d = list(deck)
    assert feasible(d), "start not feasible"
    for rnd in range(rounds):
        seed = 1000 * (rnd + 1)
        uniq = sorted(set(c for c in d if c not in protect))
        Vs = {"base": d, **{"-" + c: swap(d, c, "NOCARD") for c in uniq}}
        R = evaluate(Vs, prof, Ns, seed)
        base = R["base"]
        val = {c: pstats(base, R["-" + c])[0] for c in uniq}     # positive = card is worth keeping
        weak_nl = sorted([c for c in uniq if c not in LANDS], key=lambda c: val[c])
        weak_ld = sorted([c for c in uniq if c in LANDS], key=lambda c: val[c])
        Vs = {"base": d}
        for c in pool:
            if c in d and c != "Swamp":
                continue
            slots = weak_ld if c in LANDS else weak_nl
            for s in slots[:3]:
                x = swap(d, s, c)
                if feasible(x):
                    Vs[c] = x; break
        R2 = evaluate(Vs, prof, Ns, seed)
        gains = sorted(((pstats(R2["base"], R2[c]) , c) for c in Vs if c != "base"), key=lambda z: z[0][0])
        good = [(m, se, c) for (m, se), c in gains if m < -max(0.015, 1.5 * se)]
        log(f"round {rnd+1}: base {score(base):.3f}  weakest {[(c, round(val[c],3)) for c in weak_nl[:5]]} {[(c, round(val[c],3)) for c in weak_ld[:3]]}")
        log("   best candidates " + str([(c, round(m, 3)) for m, se, c in good[:10]]))
        if not good:
            break
        accepted = False
        for k in range(min(k_max, len(good)), 0, -1):
            x = list(d); wn = list(weak_nl); wl = list(weak_ld); used = []
            for m, se, c in good[:k]:
                slots = wl if c in LANDS else wn
                for s in list(slots):
                    y = swap(x, s, c)
                    if feasible(y):
                        x = y; slots.remove(s); used.append((s, c)); break
            if not used:
                continue
            R3 = evaluate({"base": d, "new": x}, prof, Nv, seed + 500)
            m, se = pstats(R3["base"], R3["new"])
            log(f"   try {used}: {m:+.3f}±{se:.3f}")
            if m < -max(0.01, 1.5 * se):
                d = x; accepted = True; break
        if not accepted:
            break
    return d

def report(d, prof, N=10000, ref=None):
    Vs = {"d": d} if ref is None else {"d": d, "ref": ref}
    R = evaluate(Vs, prof, N, 777)
    out = {"T4": t(R["d"], 4), "T6": t(R["d"], 6), "T8": t(R["d"], 8), "T10": t(R["d"], 10), "avg": score(R["d"])}
    if ref is not None:
        out["vs_ref"] = pstats(R["ref"], R["d"])
    return out
