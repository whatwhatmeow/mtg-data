import os
import sys, json, math, random, gzip, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..") + "/sim/vault/dusim")
from multiprocessing import Pool
from du_sim import Game, PROFILES
from du_cards import CARDS, LANDS, C
from pact_compare import version
D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..") + "/decks/doom-unrivaled.json"))
CARDS["NOCARD"] = dict(cost=C(99), type="sorcery", tags=set())
PRICE, GC, CI, LEGAL = {}, {}, {}, {}
for r in csv.DictReader(gzip.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..") + "/data/cards.csv.gz", "rt")):
    for n in {r["name"], r["name"].split(" // ")[0]}:
        GC[n] = GC.get(n) or r["game_changer"] in ("1", "1.0", "True")
        CI[n] = r["color_identity"]; LEGAL[n] = r["commander_legality"] == "legal"
        if r["price_usd"] and r["digital"] != "1":
            PRICE[n] = min(float(r["price_usd"]), PRICE.get(n, 1e9))
COMMANDER = "Doctor Doom, Unrivaled"
def price(d): return round(sum(PRICE.get(c, 0) for c in d) + PRICE[COMMANDER], 2)
def gcs(d): return [c for c in d if GC.get(c)]
def ok_card(c): return LEGAL.get(c, False) and set(CI.get(c, "X")) <= {"B"} and (c in CARDS or c in LANDS) and c not in ("NOCARD", "BLANK", "Doctor Doom, Unrivaled")
def games(deck, prof, N, seed0=0):
    return [Game(deck, PROFILES[prof], random.Random(3_000_017 * (k + 1 + seed0))).run()["win"] or 99 for k in range(N)]
def _job(a): return a[0], games(*a[1:])
def evaluate(Vs, prof, N, seed0=0):
    with Pool(2) as p:
        return dict(p.map(_job, [(n, d, prof, N, seed0) for n, d in Vs.items()], chunksize=4))
def score(r): return sum(min(x, 17) for x in r) / len(r)
def t(r, k): return 100 * sum(x <= k for x in r) / len(r)
