import os
import sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_all import *
r = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")))
# today-3gc: put the third owned Game Changer back in the weakest slot
d = r["today-3gc"]["deck"]
if len(gcs(d)) < 3:
    uniq = sorted(set(c for c in d if c not in LANDS and not GC.get(c) and c != "Tainted Pact"))
    R = evaluate({"base": d, **{c: swap(d, c, "NOCARD") for c in uniq}}, "bracket3", 2000, 4242)
    best = None
    for g in ("Orcish Bowmasters", "Opposition Agent"):
        if g in d: continue
        weak = min(uniq, key=lambda c: score(R[c]) - score(R["base"]))
        x = swap(d, weak, g)
        R2 = evaluate({"base": d, "x": x}, "bracket3", 6000, 4343)
        m = pstats(R2["base"], R2["x"])
        print("today-3gc add", g, "for", weak, m)
        if best is None or m[0] < best[0][0]: best = (m, x)
    r["today-3gc"]["deck"] = best[1]
    r["today-3gc"]["gcs"] = gcs(best[1]); r["today-3gc"]["price"] = price(best[1])
json.dump(r, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json"), "w"))
# final numbers, all on the same seeds
names = ["ideal-3gc-v2", "ideal-0gc", "budget-0gc", "budget-3gc-forced", "today-3gc", "today-0gc", "b4", "b5"]
Vs = {"Owned build (today)": version(D, "owned-build"), "Unique Pact": version(D, "unique-pact"), **{n: r[n]["deck"] for n in names}}
final = {}
for prof in ("bracket3", "bracket4", "cedh"):
    R = evaluate(Vs, prof, 10000, 777)
    final[prof] = {n: {"avg": round(score(R[n]), 2), "T4": t(R[n], 4), "T6": t(R[n], 6), "T8": t(R[n], 8), "T10": t(R[n], 10)} for n in Vs}
    print(prof, {n: (final[prof][n]["avg"], final[prof][n]["T8"]) for n in Vs})
json.dump(final, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "final.json"), "w"))
# upgrade paths: gain per dollar
def path(src, dst, label, N=3000):
    s = r[src]["deck"]; t_ = r[dst]["deck"]
    adds = [c for c in set(t_) if c not in s and c != "Swamp"]
    uniq_nl = sorted(set(c for c in s if c not in LANDS and c != "Tainted Pact"))
    uniq_ld = sorted(set(c for c in s if c in LANDS))
    R = evaluate({"base": s, **{c: swap(s, c, "NOCARD") for c in uniq_nl + uniq_ld}}, "bracket3", 2000, 5151)
    val = {c: score(R[c]) - score(R["base"]) for c in uniq_nl + uniq_ld}
    wn = sorted(uniq_nl, key=lambda c: val[c]); wl = sorted(uniq_ld, key=lambda c: val[c])
    Vs = {"base": s}
    for c in adds:
        Vs[c] = swap(s, (wl if c in LANDS else wn)[0], c)
    R2 = evaluate(Vs, "bracket3", N, 6262)
    rows = []
    for c in adds:
        m, se = pstats(R2["base"], R2[c])
        rows.append({"card": c, "cut": (wl if c in LANDS else wn)[0], "turns": round(-m, 3), "se": round(se, 3), "price": round(PRICE.get(c, 0), 2)})
    rows.sort(key=lambda z: -(z["turns"] / max(z["price"], 0.25)))
    json.dump(rows, open(f"/home/claude/work/path_{label}.json", "w"))
    print(label, rows[:12])
path("budget-0gc", "ideal-0gc", "budget_to_ideal")
path("today-0gc", "budget-0gc", "today_to_budget")
