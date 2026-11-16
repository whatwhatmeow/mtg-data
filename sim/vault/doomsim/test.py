import json, random, math, sys
from multiprocessing import Pool
import sim
from sim import Game, PROFILES
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
base = json.load(open("deck.json"))
def sw(pairs):
    d = list(base)
    for o, i in pairs:
        d[d.index(o)] = i
    return d
# (deck, use_old_coliseum_model). Edit this dict to test swaps.
V = {
 "base": (base, False),
 "Negate instead of Currency Converter": (sw([("Currency Converter", "Negate")]), False),
 "Year of Hell instead of Refute": (sw([("Refute", "Year of Hell")]), False),
 "Echo of Eons instead of Loki": (sw([("Loki, God of Mischief", "Echo of Eons")]), False),
}
def job(a):
    prof, name = a
    deck, old = V[name]
    sim.COLISEUM_EACH_PLAYER = old
    out = []
    for k in range(N):
        s = Game(deck, PROFILES[prof], random.Random(1_000_003 * (k + 1))).run()
        out.append(s["win"] or 99)
    return prof, name, out
if __name__ == "__main__":
    with Pool() as p:
        R = p.map(job, [(pr, n) for pr in ("bracket3", "bracket4") for n in V], chunksize=1)
    D = {(pr, n): r for pr, n, r in R}
    cap = lambda x: min(x, 17)
    for n in V:
        line = f"{n:40s}"
        for pr in ("bracket3", "bracket4"):
            r = D[(pr, n)]; ref = D[(pr, "base")]
            dt = [cap(x) - cap(y) for x, y in zip(r, ref)]
            m = sum(dt) / N; se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
            by12 = 100 * sum(x <= 12 for x in r) / N
            line += f" | {pr[-1]}: by12 {by12:5.1f}%  turns vs base {m:+.3f}+-{se:.3f} (negative = faster)"
        print(line, flush=True)
