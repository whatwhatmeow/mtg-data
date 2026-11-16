import json, random, math, sys
from multiprocessing import Pool
from run import base_deck
from sim import Game, PROFILES
N = 3000
base = base_deck()
CUT = ["Awesome Android", "Skirge Familiar", "Zombie Infestation", "M.O.D.O.K."]
C3 = ["Awesome Android", "Zombie Infestation", "M.O.D.O.K."]
A4 = ["Swiftfoot Boots", "Negate", "Perplex", "Muddle the Mixture"]
V = {
    "base": (None, None),
    "keep both, skip Negate": (C3, ["Swiftfoot Boots", "Perplex", "Muddle the Mixture"]),
    "keep both, cut Molten Vortex": (C3 + ["Molten Vortex"], A4),
    "keep both, cut Tectonic Reformation": (C3 + ["Tectonic Reformation"], A4),
    "keep both, cut Seismic Assault": (C3 + ["Seismic Assault"], A4),
}
def job(a):
    prof, name = a
    out, inn = V[name]
    d = list(base)
    if out:
        for o, i in zip(out, inn):
            d[d.index(o)] = i
    res = []
    for k in range(N):
        s = Game(d, PROFILES[prof], random.Random(1_000_003 * (k + 1))).run()
        res.append((s["win"] or 99, s["doom_removed"]))
    return prof, name, res
if __name__ == "__main__":
    with Pool() as p:
        R = p.map(job, [(pr, n) for pr in ("bracket3", "bracket4") for n in V], chunksize=1)
    B = {pr: r for pr, n, r in R if n == "base"}
    cap = lambda x: min(x, 17)
    for pr, n, r in R:
        b = B[pr]
        w12 = sum(1 for x, _ in r if x <= 12) / N
        w16 = sum(1 for x, _ in r if x <= 16) / N
        dt = [cap(x) - cap(y) for (x, _), (y, _) in zip(r, b)]
        m = sum(dt) / N; se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
        rem = sum(z for _, z in r) / N
        print(f"{pr:9s} {n:34s} by12 {100*w12:5.1f}%  by16 {100*w16:5.1f}%  turns vs base {m:+.2f}±{se:.2f}  Doom removed {rem:.2f}")
