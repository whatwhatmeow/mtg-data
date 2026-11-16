import json, random, math, statistics
from multiprocessing import Pool
from sim import Game, PROFILES
N = 3000
d = json.load(open("/tmp/claude-0/-home-claude/850d6bd5-0d1f-5929-829a-e94d62201355/scratchpad/doom-update2.json"))
base = [c["name"] for c in d["cards"] for _ in range(c.get("qty", 1))]
def sw(deck, pairs):
    x = list(deck)
    for o, i in pairs:
        x[x.index(o)] = i
    return x
CORE = [("Talisman of Indulgence", "Mana Vault"), ("Talisman of Creativity", "Chrome Mox"),
        ("Chromatic Lantern", "Mox Diamond"), ("Mountain", "Ancient Tomb"), ("Skirge Familiar", "Grim Monolith"),
        ("Arcane Denial", "Force of Will"), ("Green Goblin, Nemesis", "Demonic Tutor"),
        ("Chaos Warp", "Vampiric Tutor"), ("Taskmaster, Mercenary Mimic", "Gamble")]
MAX = CORE + [("Irma, Part-Time Mutant", "Imperial Seal"), ("Archfiend of Ifnir", "Mystical Tutor"),
              ("Psychosis Crawler", "Rhystic Study"), ("Chameleon, Master of Disguise", "The One Ring"),
              ("Negate", "Fierce Guardianship"), ("Living Laser", "Necropotence")]
V = {"current list (3 Game Changers)": base,
     "Bracket 4 core (+9: fast mana, FoW, 3 tutors)": sw(base, CORE),
     "Bracket 4 max (+15)": sw(base, MAX)}
def job(a):
    prof, name = a
    out = []
    for k in range(N):
        s = Game(V[name], PROFILES[prof], random.Random(1_000_003 * (k + 1))).run()
        out.append((s["win"] or 99, s["engine"] or 99, s["doom_removed"]))
    return prof, name, out
if __name__ == "__main__":
    with Pool() as p:
        R = p.map(job, [(pr, n) for pr in ("bracket3", "bracket4") for n in V], chunksize=1)
    B = {pr: r for pr, n, r in R if n.startswith("current")}
    cap = lambda x: min(x, 17)
    for pr, n, r in R:
        dt = [cap(x[0]) - cap(y[0]) for x, y in zip(r, B[pr])]
        m = sum(dt) / N; se = math.sqrt(sum((v - m) ** 2 for v in dt) / (N - 1) / N)
        wins = [x[0] for x in r if x[0] <= 16]
        eng = [x[1] for x in r if x[1] < 99]
        print(f"{pr:9s} {n:46s} by6 {100*sum(x[0]<=6 for x in r)/N:4.1f}% by8 {100*sum(x[0]<=8 for x in r)/N:4.1f}% by10 {100*sum(x[0]<=10 for x in r)/N:5.1f}% by12 {100*sum(x[0]<=12 for x in r)/N:5.1f}% by16 {100*len(wins)/N:5.1f}% | avg win T {statistics.mean(wins):.1f} | engine online median T{statistics.median(eng)} | vs current {m:+.2f}±{se:.2f}")
