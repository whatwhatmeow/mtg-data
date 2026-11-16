import json, random, statistics, sys
from collections import Counter
from sim import Game, PROFILES, DOOM
from cards import LANDS, CARDS

VAULT = sys.argv[1] if len(sys.argv) > 1 else "doctor-doom.json"


def base_deck():
    d = json.load(open(VAULT))
    deck = []
    for c in d["cards"]:
        deck += [c["name"]] * c.get("qty", 1)
    assert len(deck) == 99, len(deck)
    missing = [c for c in set(deck) if c not in LANDS and c not in CARDS]
    assert not missing, missing
    return deck


def variant(deck, out, inn):
    deck = list(deck)
    for c in out:
        deck.remove(c)
    deck += inn
    assert len(deck) == 99
    return deck


def run(deck, profile, n=1000, seed=1):
    rng = random.Random(seed)
    res = [Game(deck, PROFILES[profile], rng).run() for _ in range(n)]
    return res


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def summarize(res, max_turn=16):
    n = len(res)
    out = {}
    for key in ("engine", "inevitable", "win"):
        xs = [r[key] for r in res if r[key] is not None]
        out[key] = dict(rate=len(xs) / n, median=statistics.median(xs) if xs else None,
                        mean=round(statistics.mean(xs), 2) if xs else None,
                        p25=pct(xs, .25) if xs else None, p75=pct(xs, .75) if xs else None)
    hows = Counter(r["how"] for r in res)
    out["how"] = {k or "no win by T16": v for k, v in hows.items()}
    out["by_turn"] = {t: sum(1 for r in res if r["win"] and r["win"] <= t) / n for t in (6, 7, 8, 9, 10, 12)}
    out["doom_removed"] = round(sum(r["doom_removed"] for r in res) / n, 2)
    out["stopped"] = round(sum(r["removal_stopped"] for r in res) / n, 2)
    out["doom_casts"] = round(sum(r["doom_casts"] for r in res) / n, 2)
    bu = [r for r in res if r["boots_used"]]
    out["boots_games"] = len(bu) / n
    if bu:
        out["boots_win_by12"] = sum(1 for r in bu if r["win"] and r["win"] <= 12) / len(bu)
        nb = [r for r in res if not r["boots_used"]]
        out["noboots_win_by12"] = sum(1 for r in nb if r["win"] and r["win"] <= 12) / len(nb)
    return out


if __name__ == "__main__":
    base = base_deck()
    V = {
        "A. Current list": base,
        "B. -M.O.D.O.K. +Swiftfoot Boots": variant(base, ["M.O.D.O.K."], ["Swiftfoot Boots"]),
        "C. -M.O.D.O.K. -Living Laser +Boots +Negate": variant(base, ["M.O.D.O.K.", "Living Laser"], ["Swiftfoot Boots", "Negate"]),
        "D. -Living Laser -Norman +Boots +Negate (keep MODOK)": variant(base, ["Living Laser", "Norman Osborn // Green Goblin"], ["Swiftfoot Boots", "Negate"]),
        "E. Heavy: -Laser -Norman -Goblin Nemesis -Android +Boots +Greaves +Negate +Deflecting Swat": variant(base, ["Living Laser", "Norman Osborn // Green Goblin", "Green Goblin, Nemesis", "Awesome Android"], ["Swiftfoot Boots", "Lightning Greaves", "Negate", "Deflecting Swat"]),
    }
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    results = {}
    for prof in ("bracket3", "bracket4"):
        for name, deck in V.items():
            s = summarize(run(deck, prof, n=n, seed=42))
            results[f"{prof} | {name}"] = s
            print(prof, "|", name)
            print("  ", json.dumps(s))
    json.dump(results, open("results.json", "w"), indent=1)
