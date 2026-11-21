import os
import sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from opt import *
UP = version(D, "unique-pact")
OB = version(D, "owned-build")
AB = list(UP)
for o, i in [("Rat King, Verminister","Wishclaw Talisman"),("Chromatic Star","Inverter of Truth"),("Rescue from the Underworld","Beseech the Queen"),
             ("Phyrexian Scriptures","Dark Petition"),("Breach the Multiverse","Charcoal Diamond"),("Arc Reactor","Demonic Consultation"),
             ("Rat King, Pale Piper","Scheming Symmetry"),("Grim Reaper's Scythe","Lavaspur Boots")]:
    AB = swap(AB, o, i)
BUDGET = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cA_final.json")))
SLEEVED = ["Adaptive Omnitool","Age of Ultron","Animate Dead","Arcane Signet","Big Mother Mouser","Breach the Multiverse","Buried Alive","Castle Doom","Codex Shredder","Cranial Plating","Dark Ritual","Deadly Dispute","Diabolic Tutor","Doctor Doom","Doom Blade","Doom's Servo-Guards","Doombot Harbinger","Doomfall","Doomsday","Exsanguinate","Genesis of the Daleks","Go for the Throat","Grim Reaper's Scythe","Horn of Greed","Idol of Oblivion","Kingpin, Wilson Fisk","Lash of the Balrog","Leaden Myr","Leveler","Lightning Greaves","Liquimetal Torque","Mask of Memory","Memorial to Folly","Millikin","Millstone","Nasty End","Night's Whisper","Persist","Phyrexian Arena","Phyrexian Scriptures","Project Deathlok Soldier","Psychosis Crawler","Rat King, Pale Piper","Rat King, Verminister","Read the Bones","Rogue's Passage","Shred Memory","Sol Ring","Splinter's Technique","Spymaster's Vault","Stargaze","The War in Heaven","Ultron the Annihilator","Ultron, Artificial Malevolence","Vault of Whispers","Victimize","Withering Torment","Zombie Infestation"]
MEM = ["Demonic Tutor","Tainted Pact","The One Ring","Orcish Bowmasters","Opposition Agent","Leyline of the Void","Toxic Deluge","Darksteel Plate","Black Vise","Skullcage","Nettlecyst","Black Market Connections","Mind Stone","Skullclamp","Grim Discovery","Shadow of the Grave","Cabal Ritual","Feed the Swarm","Reanimate","Sign in Blood","Diabolic Tutor","Evolving Wilds","Terramorphic Expanse","Vibrant Cityscape","Champion's Helm","Peter Parker's Camera","Thriving Moor","Unclaimed Territory","Eumidian Hatchery"]
ADDS = [a["name"] for a in D["adds"] if a["status"] in ("owned", "Borg (unopened)")]
OWNED = set(OB) | set(SLEEVED) | set(MEM) | set(ADDS) | {"Swamp"}
OWNED = {c for c in OWNED if ok_card(c)}
BAD = {"Spoils of the Vault"}           # model ignores its life loss
POOL = sorted(c for c in set(CARDS) | set(LANDS) if ok_card(c) and c not in BAD)
def singleton(d): return len(d) == 99 and all(n == 1 for c, n in __import__("collections").Counter(d).items() if c != "Swamp")
def F(maxgc=None, gc0=False, cap=None, owned=False):
    def f(d):
        if not singleton(d): return False
        g = len(gcs(d))
        if gc0 and g: return False
        if maxgc is not None and g > maxgc: return False
        if cap is not None and price(d) > cap: return False
        if owned and not all(c in OWNED for c in d): return False
        return True
    return f
def addgc(d, picks, slots):
    for p, s in zip(picks, slots): d = swap(d, s, p)
    return d
if __name__ == "__main__":
    which = sys.argv[1:]
    res = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json"))) if __import__("os").path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")) else {}
    logf = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build.log"), "a")
    def log(s): print(s); logf.write(s + "\n"); logf.flush()
    jobs = {
     "ideal-3gc": (lambda: addgc(AB, ["Demonic Tutor","Chrome Mox","Vampiric Tutor"], ["Mask of Memory","Doomfall","Age of Ultron"]), "bracket3", F(maxgc=3), POOL),
     "ideal-0gc": (lambda: AB, "bracket3", F(gc0=True), POOL),
     "budget-0gc": (lambda: BUDGET, "bracket3", F(gc0=True, cap=150), [c for c in POOL if PRICE.get(c, 99) <= 6]),
     "budget-3gc": (lambda: None, "bracket3", F(maxgc=3, cap=150), [c for c in POOL if PRICE.get(c, 99) <= 25]),
     "today-0gc": (lambda: OB, "bracket3", F(gc0=True, owned=True), sorted(OWNED)),
     "today-3gc": (lambda: addgc(OB, ["Demonic Tutor","The One Ring","Orcish Bowmasters"], ["Mask of Memory","Chromatic Sphere","Rat King, Verminister"]), "bracket3", F(maxgc=3, owned=True), sorted(OWNED)),
     "b4": (lambda: json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")).read())["ideal-3gc-v2"]["deck"], "bracket4", F(), POOL),
     "ideal-3gc-v2": (lambda: addgc(json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")).read())["ideal-0gc"]["deck"], ["Demonic Tutor","Chrome Mox","Vampiric Tutor"], ["Stargaze","Duress","The War in Heaven"]), "bracket3", F(maxgc=3), POOL),
     "budget-3gc-forced": (lambda: None, "bracket3", (lambda d: F(maxgc=3, cap=150)(d) and len(gcs(d)) == 3), [c for c in POOL if PRICE.get(c, 99) <= 25 and not GC.get(c)]),
     "b5": (lambda: json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")).read())["b4"]["deck"], "cedh", F(), POOL),
    }
    for w in which:
        mk, prof, feas, pool = jobs[w]
        start = mk()
        if w in ("budget-3gc", "budget-3gc-forced"):
            start = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")).read())["budget-0gc"]["deck"]
            # make room for three cheap Game Changers by cutting the priciest non-core cards
            for g, s in zip(["Ad Nauseam", "Bolas's Citadel", "Opposition Agent"], ["Mask of Memory", "Doom Blade", "Nasty End"]):
                if s in start: start = swap(start, s, g)
            core = {"Tainted Pact", "Doctor Doom", "Ad Nauseam", "Bolas's Citadel", "Opposition Agent"}
            cheap = [c for c in sorted(pool, key=lambda c: PRICE.get(c, 99)) if c not in start and c not in LANDS and not GC.get(c)]
            while price(start) > 150:
                ex = max((c for c in set(start) if c not in core and c != "Swamp"), key=lambda c: PRICE.get(c, 0))
                start = swap(start, ex, "Swamp" if ex in LANDS else cheap.pop(0))
        log(f"=== {w} start: price {price(start)}  GCs {gcs(start)}  feasible {feas(start)}")
        d = optimize(start, prof, feas, pool, log=log, protect=("Ad Nauseam", "Bolas's Citadel", "Opposition Agent") if w == "budget-3gc-forced" else ())
        rep = report(d, prof, ref=UP)
        res[w] = {"deck": d, "price": price(d), "gcs": gcs(d), "report": rep, "profile": prof}
        log(f"=== {w} done: price {price(d)} GCs {gcs(d)} {rep}")
        json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json"), "w"))
