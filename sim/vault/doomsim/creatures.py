import json, random, math
from multiprocessing import Pool
from sim import Game, PROFILES
from cards import CARDS
N = 3000
d = json.load(open("/tmp/claude-0/-home-claude/850d6bd5-0d1f-5929-829a-e94d62201355/scratchpad/doom-update2.json"))
base = [c["name"] for c in d["cards"] for _ in range(c.get("qty", 1))]
creatures = ["Psychic Frog", "Skirge Familiar", "Bone Miser", "Tinybones, Pocket Nuisance"]
V = {"base": base}
for c in creatures:
    x = list(base); x[x.index(c)] = "BLANK"; V[c] = x
STATS = []
def job(a):
    prof, name = a
    out = []
    global FROG
    for k in range(N):
        s = Game(V[name], PROFILES[prof], random.Random(1_000_003 * (k + 1))).run()
        out.append(s["win"] or 99)
        if name == "base":
            STATS.append((s.get("frog_dmg", 0), s.get("frog_draws", 0)))
    if name == "base":
        print(prof, "Frog: avg combat dmg/game %.1f, avg draws/game %.2f, max dmg %d" % (sum(a for a,_ in STATS)/N, sum(b for _,b in STATS)/N, max(a for a,_ in STATS)), flush=True)
    return prof, name, out
if __name__ == "__main__":
    with Pool() as p:
        R = p.map(job, [(pr, n) for pr in ("bracket3", "bracket4") for n in V], chunksize=1)
    B = {pr: r for pr, n, r in R if n == "base"}
    cap = lambda x: min(x, 17)
    for pr in B: print(pr, "baseline by10 %.1f%% by12 %.1f%% by16 %.1f%%" % (100*sum(x<=10 for x in B[pr])/N, 100*sum(x<=12 for x in B[pr])/N, 100*sum(x<=16 for x in B[pr])/N))
    res = {}
    for pr, n, r in R:
        if n == "base": continue
        dt = [cap(x) - cap(y) for x, y in zip(r, B[pr])]
        m = sum(dt) / N; se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
        res.setdefault(n, {})[pr] = (m, se, 100 * (sum(y <= 12 for y in B[pr]) - sum(x <= 12 for x in r)) / N)
    for n in sorted(res, key=lambda n: -(res[n]["bracket3"][0] + res[n]["bracket4"][0])):
        a, b = res[n]["bracket3"], res[n]["bracket4"]
        print(f"{n:34s} B3 {a[0]:+.3f}±{a[1]:.3f} (by12 {a[2]:+.1f}pts)   B4 {b[0]:+.3f}±{b[1]:.3f} (by12 {b[2]:+.1f}pts)")
